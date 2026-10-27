# Decisions

- The scorer is exact tool name plus arguments. Success also requires no stagnation and no tool error. Stagnation is the same call twice in a row, or a failed call issued again later.
- Held-out tools, absent from train gold: lookup_customer_by_email, quote_refund, escalate.
- Train gold is the specification. It is not a measured model result. Blind numbers are reported on the transfer split.
- The later training target is Qwen/Qwen3-1.7B, Apache-2.0, in a free notebook. Not before M4, and not without an explicit go-ahead.
- No paid model API.
- This repository has one author, listed in config/author.
- The set is 16 train tasks and 8 transfer tasks.
