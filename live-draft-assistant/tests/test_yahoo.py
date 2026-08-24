import sys
import types

import pytest

xmltodict_stub = types.ModuleType("xmltodict")
xmltodict_stub.parse = lambda value: value  # type: ignore[attr-defined]
sys.modules.setdefault("xmltodict", xmltodict_stub)

from app.yahoo import YahooClient


@pytest.mark.asyncio
async def test_draft_results_parses_and_sorts(tmp_path) -> None:
    client = YahooClient(
        client_id="id",
        client_secret="secret",
        redirect_uri="http://localhost/callback",
        token_path=tmp_path / "token.json",
    )

    async def fake_get_xml(path: str):
        assert path.endswith("/draftresults")
        return {
            "fantasy_content": {
                "league": {
                    "draft_results": {
                        "0": {
                            "draft_result": {
                                "pick": "2",
                                "round": "1",
                                "team_key": "461.l.810161.t.2",
                                "player_id": "999",
                            }
                        },
                        "1": {
                            "draft_result": {
                                "pick": "1",
                                "round": "1",
                                "team_key": "461.l.810161.t.1",
                                "player_id": "888",
                            }
                        },
                    }
                }
            }
        }

    client.get_xml = fake_get_xml  # type: ignore[method-assign]
    picks = await client.draft_results("461.l.810161")
    assert [pick.pick for pick in picks] == [1, 2]
    assert picks[0].player_id == "888"
