# Papers this experiment follows

A small open model should select and sequence tools on a corpus it was not trained on, without repeating a failed call.

- Tool selection. Zhou et al., 22 October 2026, [arXiv:2610.31483](https://arxiv.org/abs/2610.31483). Qwen3 models from 1.7B to 8B, after supervised traces and then GRPO, beat Llama-4-Maverick (402B) on ToolBench G3. The checkpoint transfers to a new tool corpus and a new retriever. Target checkpoint: Qwen/Qwen3-1.7B, Apache-2.0.
- Distill recorded behavior, not a synthetic imitation. Wang, [arXiv:2610.14576](https://arxiv.org/abs/2610.14576), NeurIPS 2026 workshop. Freeze the behavior, log the real decisions, LoRA-tune the small model. Here the recorded decisions are solutions of instructions whose gold calls were not visible.
- Stagnation. Cao et al., October 2026, [arXiv:2610.19439](https://arxiv.org/abs/2610.19439). Distilled models from 0.6B to 8B repeat a failed strategy. The scorer flags a repeated tool call with the same arguments, including a failed call issued again later.

Constraints for this repository:

- No paid model API.
- No weight update before the notebook in STATUS.md, and no credential in the tree.
- The scorer stays fixed. A change to it is a separate decision, written down in docs/DECISIONS.md.
