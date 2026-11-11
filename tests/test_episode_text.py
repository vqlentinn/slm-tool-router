from toolrouter.episode_text import format_episode, parse_tool_calls, prompt_for


def test_prompt_is_the_training_prefix():
    instruction = "Ada (customer ada) wants a full refund of order A100."
    calls = [
        {"tool": "lookup_order", "args": {"order_id": "A100"}},
        {"tool": "issue_refund", "args": {"order_id": "A100", "amount_eur": 40}},
    ]
    episode = format_episode(instruction, calls)
    prompt = prompt_for(instruction)
    assert episode.startswith(prompt)
    assert parse_tool_calls(episode.split("<|assistant|>\n", 1)[1]) == calls


def test_parser_stops_after_the_call_block():
    text = "TOOL quote_refund {'order_id': 'D400'}\nnot a call\nTOOL escalate {'reason': 'x'}\n"
    assert parse_tool_calls(text) == [
        {"tool": "quote_refund", "args": {"order_id": "D400"}}
    ]


def test_unparseable_arguments_become_an_empty_dict():
    assert parse_tool_calls("TOOL lookup_order not-a-dict\n") == [
        {"tool": "lookup_order", "args": {}}
    ]
