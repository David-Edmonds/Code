from app.models import Player
from app.rankings import merge_rankings


def test_merge_rankings_combines_sources() -> None:
    custom = [Player(name="CeeDee Lamb", position="WR", team="DAL", custom_rank=8, source="ECR")]
    yahoo = [Player(name="CeeDee Lamb", position="WR", team="DAL", yahoo_rank=6, yahoo_id="123", source="Yahoo")]
    adp = [Player(name="CeeDee Lamb", position="WR", team="DAL", adp=7.2, source="ADP")]
    merged = merge_rankings(custom, yahoo, adp)
    assert len(merged) == 1
    assert merged[0].custom_rank == 8
    assert merged[0].yahoo_rank == 6
    assert merged[0].adp == 7.2
    assert merged[0].yahoo_id == "123"
