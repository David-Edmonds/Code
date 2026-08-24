from __future__ import annotations

import base64
import json
import secrets
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

import httpx
import xmltodict

from .models import DraftPick, Player
from .utils import ensure_list, find_all, first_scalar, safe_int

AUTH_URL = "https://api.login.yahoo.com/oauth2/request_auth"
TOKEN_URL = "https://api.login.yahoo.com/oauth2/get_token"
FANTASY_BASE = "https://fantasysports.yahooapis.com/fantasy/v2"


class YahooError(RuntimeError):
    pass


class YahooClient:
    def __init__(
        self,
        *,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        token_path: Path,
    ) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.token_path = token_path

    @property
    def configured(self) -> bool:
        return bool(self.client_id and self.client_secret and self.redirect_uri)

    @property
    def authenticated(self) -> bool:
        token = self._load_token()
        return bool(token and (token.get("access_token") or token.get("refresh_token")))

    def authorization_url(self) -> tuple[str, str]:
        if not self.configured:
            raise YahooError("Yahoo OAuth credentials are not configured")
        state = secrets.token_urlsafe(24)
        query = urlencode(
            {
                "client_id": self.client_id,
                "redirect_uri": self.redirect_uri,
                "response_type": "code",
                "language": "en-us",
                "state": state,
            }
        )
        return f"{AUTH_URL}?{query}", state

    async def exchange_code(self, code: str) -> dict[str, Any]:
        token = await self._token_request(
            {
                "grant_type": "authorization_code",
                "redirect_uri": self.redirect_uri,
                "code": code,
            }
        )
        self._save_token(token)
        return token

    async def refresh(self) -> dict[str, Any]:
        existing = self._load_token() or {}
        refresh_token = existing.get("refresh_token")
        if not refresh_token:
            raise YahooError("No Yahoo refresh token is available")
        token = await self._token_request(
            {
                "grant_type": "refresh_token",
                "redirect_uri": self.redirect_uri,
                "refresh_token": refresh_token,
            }
        )
        if not token.get("refresh_token"):
            token["refresh_token"] = refresh_token
        self._save_token(token)
        return token

    async def _token_request(self, data: dict[str, str]) -> dict[str, Any]:
        basic = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(
                TOKEN_URL,
                data=data,
                headers={
                    "Authorization": f"Basic {basic}",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
            )
        if response.status_code >= 400:
            message = f"Yahoo token request failed: {response.status_code} {response.text[:300]}"
            raise YahooError(message)
        return response.json()

    async def get_xml(self, path: str) -> dict[str, Any]:
        token = await self._valid_token()
        async with httpx.AsyncClient(timeout=25, follow_redirects=True) as client:
            response = await client.get(
                f"{FANTASY_BASE}{path}",
                headers={"Authorization": f"Bearer {token['access_token']}"},
            )
        if response.status_code == 401:
            token = await self.refresh()
            async with httpx.AsyncClient(timeout=25, follow_redirects=True) as client:
                response = await client.get(
                    f"{FANTASY_BASE}{path}",
                    headers={"Authorization": f"Bearer {token['access_token']}"},
                )
        if response.status_code >= 400:
            raise YahooError(f"Yahoo API failed: {response.status_code} {response.text[:400]}")
        parsed = xmltodict.parse(response.text)
        return parsed

    async def discover_league_key(self, league_id: str) -> str:
        payload = await self.get_xml("/users;use_login=1/games;game_codes=nfl/leagues")
        for league in find_all(payload, "league"):
            if not isinstance(league, dict):
                continue
            current_id = first_scalar(league.get("league_id"))
            if current_id == str(league_id):
                league_key = first_scalar(league.get("league_key"))
                if league_key:
                    return league_key
        raise YahooError(f"League ID {league_id} was not found in the connected Yahoo account")

    async def league_settings(self, league_key: str) -> dict[str, Any]:
        payload = await self.get_xml(f"/league/{league_key}/settings")
        settings_nodes = find_all(payload, "settings")
        return settings_nodes[0] if settings_nodes and isinstance(settings_nodes[0], dict) else {}

    async def draft_results(self, league_key: str) -> list[DraftPick]:
        payload = await self.get_xml(f"/league/{league_key}/draftresults")
        results = find_all(payload, "draft_result")
        picks: list[DraftPick] = []
        for item in results:
            if not isinstance(item, dict):
                continue
            pick = safe_int(first_scalar(item.get("pick")))
            round_number = safe_int(first_scalar(item.get("round")))
            if pick is None:
                continue
            picks.append(
                DraftPick(
                    pick=pick,
                    round=round_number or 0,
                    team_key=first_scalar(item.get("team_key")),
                    player_name="",
                    player_id=first_scalar(item.get("player_id")) or None,
                )
            )
        picks.sort(key=lambda value: value.pick)
        return picks

    async def player_details(self, league_key: str, player_ids: list[str]) -> dict[str, Player]:
        if not player_ids:
            return {}
        game_key = league_key.split(".", 1)[0]
        output: dict[str, Player] = {}
        for start in range(0, len(player_ids), 25):
            batch = player_ids[start : start + 25]
            keys = ",".join(f"{game_key}.p.{player_id}" for player_id in batch)
            payload = await self.get_xml(f"/league/{league_key}/players;player_keys={keys}")
            for item in find_all(payload, "player"):
                parsed = self._parse_player(item)
                if parsed.yahoo_id:
                    output[parsed.yahoo_id] = parsed
        return output

    async def available_players(self, league_key: str, limit: int = 250) -> list[Player]:
        players: list[Player] = []
        start = 0
        batch_size = 25
        while start < limit:
            payload = await self.get_xml(
                f"/league/{league_key}/players;status=A;sort=OR;start={start};count={batch_size}"
            )
            batch = [self._parse_player(item) for item in find_all(payload, "player")]
            if not batch:
                break
            for index, player in enumerate(batch, start=start + 1):
                player.yahoo_rank = float(index)
                player.source = "Yahoo league rank"
            players.extend(batch)
            if len(batch) < batch_size:
                break
            start += batch_size
        return players[:limit]

    def _parse_player(self, item: Any) -> Player:
        if not isinstance(item, dict):
            return Player(name="Unknown", position="")
        name_node = item.get("name") if isinstance(item.get("name"), dict) else {}
        bye_nodes = ensure_list(item.get("bye_weeks"))
        bye_week = None
        if bye_nodes and isinstance(bye_nodes[0], dict):
            bye_week = safe_int(first_scalar(bye_nodes[0].get("week")))
        return Player(
            name=first_scalar(name_node.get("full")) or first_scalar(item.get("name")) or "Unknown",
            position=first_scalar(item.get("display_position")).split(",")[0].upper(),
            team=first_scalar(item.get("editorial_team_abbr"), "FA").upper(),
            yahoo_id=first_scalar(item.get("player_id")) or None,
            injury_status=first_scalar(item.get("status")) or None,
            injury_note=first_scalar(item.get("injury_note")) or None,
            bye_week=bye_week,
        )

    async def _valid_token(self) -> dict[str, Any]:
        token = self._load_token()
        if not token:
            raise YahooError("Yahoo is not authenticated")
        if float(token.get("expires_at", 0)) <= time.time() + 60:
            token = await self.refresh()
        return token

    def _load_token(self) -> dict[str, Any] | None:
        if not self.token_path.exists():
            return None
        try:
            return json.loads(self.token_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None

    def _save_token(self, token: dict[str, Any]) -> None:
        expires_in = int(token.get("expires_in", 3600))
        token["expires_at"] = time.time() + expires_in
        self.token_path.parent.mkdir(parents=True, exist_ok=True)
        self.token_path.write_text(json.dumps(token, indent=2), encoding="utf-8")
