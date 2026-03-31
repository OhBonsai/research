# Research: OpenClaw Memory Implementation and Popular Agent Frameworks Memory Systems (2025-2026)

**Date**: 2026-03-30
**Research Focus**: Understanding memory architectures in modern agent frameworks, with specific emphasis on OpenClaw's approach and comparative analysis of top agent frameworks.

---

## Part 1: OpenClaw Memory Implementation

### Overview
OpenClaw is an open-source AI agent framework that has become prominent as of late 2025/early 2026. It stores agent memory as plain Markdown files in the workspace, with the files serving as the source of truth rather than the model maintaining learned weights.

Sources:
- [Memory - OpenClaw Official Docs](https://docs.openclaw.ai/concepts/memory)
- [OpenClaw Memory Masterclass: The complete guide to agent memory that survives](https://velvetshark.com/openclaw-memory-masterclass)
- [What Is OpenClaw? Complete Guide to the Open-Source AI Agent](https://milvus.io/blog/openclaw-formerly-clawdbot-moltbot-explained-a-complete-guide-to-the-autonomous-ai-agent.md)
- [Your OpenClaw Agent Has Amnesia. Here Is the Permanent Memory Fix.](https://www.roborhythms.com/openclaw-permanent-memory-setup/)
- [OpenClaw Architecture - Part 3: Memory and State Ownership](https://openclaw.substack.com/p/openclaw-architecture-part-3-memory)

### Core Memory Architecture

**Storage Model**: Plain Markdown files in the workspace
- MEMORY.md contains curated long-term memory, decisions, preferences, and durable facts
- memory/YYYY-MM-DD.md contains day-to-day notes and running context (append-only daily logs)
- Files are the actual source of truth; the model only "remembers" what's written to disk

**Key Design Principle**: State ownership + rehydration
- The interesting work is deciding what survives, where it lives, who can write it, and how it gets injected back without blowing up latency, cost, or safety
- Memory isn't model learning; it's explicit persistent state management

### Memory Tools

OpenClaw exposes two agent-facing tools for Markdown files:
1. **memory_search** — semantic recall over indexed snippets
2. **memory_get** — targeted read of a specific Markdown file or line range

Sources:
- [GitHub - supermemoryai/openclaw-supermemory](https://github.com/supermemoryai/openclaw-supermemory)
- [We Extracted OpenClaw's Memory System and Open-Sourced It (memsearch)](https://milvus.io/blog/we-extracted-openclaws-memory-system-and-opensourced-it-memsearch.md)

### Pre-Compaction Memory Flush

When a session approaches auto-compaction, OpenClaw triggers a silent agentic turn that reminds the model to write durable memory before the context is compacted. This ensures critical information persists before aggressive context compression.

### Isolation Mechanisms

Sources:
- [OpenClaw security: architecture and hardening guide](https://nebius.com/blog/posts/openclaw-security)
- [OpenClaw Architecture, Explained: How It Works](https://ppaolo.substack.com/p/openclaw-system-architecture-overview)
- [Deep Dive into OpenClaw Architecture: Technical Principles and Extension Practices](https://eastondev.com/blog/en/posts/ai/20260205-openclaw-architecture-guide/)
- [Decoding OpenClaw: The Surprising Elegance of Two Simple Abstractions](https://binds.ch/blog/openclaw-systems-analysis/)

**Session Isolation**
- Per-channel-peer mode where each user has independent sessions
- Main session handles direct messages; group/channel interactions create separate sessions
- Prevents context confusion across different communication channels

**Tool Execution Sandboxing**
- Host execution (default for main session)
- Docker container isolation for group chats and secondary threads
- Non-main sessions run in isolated containers; primary session on host
- Docker mode provides fresh containers with limited filesystem access

**Canvas Isolation**
- Canvas separated from main Gateway provides isolation
- Gateway continues operating if Canvas crashes
- Different security boundary since Canvas serves agent-writable content

**Plugin Isolation**
- Specialized runtime for plugins isolated from main process
- Access to Gateway services while maintaining process isolation

### GitHub and Academic Resources

Sources:
- [GitHub - Gen-Verse/OpenClaw-RL: Train any agent simply by talking](https://github.com/Gen-Verse/OpenClaw-RL)
- [OpenClaw Organizations on GitHub](https://github.com/openclaw)
- [Uncovering Security Threats and Architecting Defenses in Autonomous Agents: A Case Study of OpenClaw (arXiv)](https://arxiv.org/html/2603.12644v1)
- [Don't Let the Claw Grip Your Hand: A Security Analysis and Defense Framework for OpenClaw (arXiv)](https://arxiv.org/html/2603.10387v1)
- [OpenClaw-RL: Train Any Agent Simply by Talking (arXiv 2603.10165)](https://arxiv.org/abs/2603.10165)

---

## Part 2: Popular Agent Frameworks Memory Implementations (2025-2026)

### 1. Claude Code (Anthropic)

**Storage**: Files-based (.claude/projects/<project>/memory/)
**Memory File**: MEMORY.md (first 200 lines or 25KB loaded per session)

Sources:
- [How Claude remembers your project - Claude Code Docs](https://code.claude.com/docs/en/memory)
- [Anthropic Just Added Auto-Memory to Claude Code — MEMORY.md](https://medium.com/@joe.njenga/anthropic-just-added-auto-memory-to-claude-code-memory-md-i-tested-it-0ab8422754d2)
- [Claude Code Auto Memory: How Your AI Learns Your Project](https://claudefa.st/blog/guide/mechanics/auto-memory)
- [Claude Code Dreams: Anthropic's New Memory Feature](https://claudefa.st/blog/guide/mechanics/auto-dream)
- [GitHub - thedotmack/claude-mem: Automatically captures everything Claude does](https://github.com/thedotmack/claude-mem)
- [The CLAUDE.md Memory System - Deep Dive](https://institute.sfeir.com/en/claude-code/claude-code-memory-system-claude-md/deep-dive/)

**Key Features**:
- Auto-memory captures project knowledge automatically (build commands, debugging insights, architecture notes, code style)
- Project-specific memory directory with MEMORY.md entrypoint
- Smart updates: Claude decides what's worth remembering based on usefulness in future conversations
- v2.1.59+ required; enabled by default (disable via CLAUDE_CODE_DISABLE_AUTO_MEMORY=1)
- Durable project knowledge that persists regardless of which conversation produced it

**Memory Lifecycle**:
- Creation: Automatic as Claude works
- Update: Selective based on relevance heuristics
- Retrieval: First 200 lines loaded at session start
- Decay: Not explicitly mentioned; content removal is manual

---

### 2. Cursor (Anysphere)

**Storage**: .cursorrules file (single) or .cursor/rules/ directory (structured)
**Implementation**: Text files injected into system prompt

Sources:
- [Mastering Cursor Rules: The Ultimate Guide to .cursorrules and Memory Bank](https://dev.to/pockit_tools/mastering-cursor-rules-the-ultimate-guide-to-cursorrules-and-memory-alm)
- [Advanced Cursor: Use the Memory bank to eliminate hallucination](https://medium.com/codetodeploy/advanced-cursor-use-the-memory-bank-to-eliminate-hallucination-affd3fbeefa3)
- [Cursor Memory Bank - GitHub Gist](https://gist.github.com/ipenywis/1bdb541c3a612dbac4a14e1e3f4341ab)
- [GitHub - vanzan01/cursor-memory-bank: Modular documentation-driven framework](https://github.com/vanzan01/cursor-memory-bank)
- [How to Supercharge AI Coding with Cursor Rules and Memory Banks](https://www.lullabot.com/articles/supercharge-your-ai-coding-cursor-rules-and-memory-banks)
- [Cursor .cursorrules File: Project-Specific AI Instructions Guide](https://markaicode.com/cursorrules-project-ai-instructions-guide/)

**Key Features**:
- .cursorrules file automatically detected and injected into every system prompt
- New .cursor/rules/ directory system for better organization and contextual application
- Memory Bank pattern: techContext.md, systemPatterns.md, activeContext.md, progress.md
- Text-based rules, not learned weights
- Integration via specialized commands that read from and update Memory Bank directories

**Memory Lifecycle**:
- Creation: Manual file creation
- Update: Static files (techContext) or frequently updated (activeContext, progress)
- Retrieval: Injected into system prompt for every request
- Decay: Manual deletion or file-based lifecycle

---

### 3. Devin (Cognition)

**Storage**: Structured files (notes.txt, knowledge entries, codebase index)
**Implementation**: File-based context + knowledge base system

Sources:
- [Devin AI review 2025: I tested it for 5 days](https://techpoint.africa/guide/devin-ai-review/)
- [Devin AI Complete Guide: Autonomous Software Engineering](https://www.digitalapplied.com/blog/devin-ai-autonomous-coding-complete-guide/)
- [Recent Updates - Devin Docs](https://docs.devin.ai/release-notes/overview/)
- [Cognition | Devin's 2025 Performance Review: Learnings From 18 Months of Agents At Work](https://cognition.ai/blog/devin-annual-performance-review-2025/)
- [Devin: A Viral AI Coding Agent: Everything You Need to Know](https://thinkml.ai/devin-a-viral-ai-coding-agent-everything-you-need-to-know/)

**Key Features**:
- notes.txt logs thoughts ("User wants X", "We're doing Y", "I hit issue Z")
- Structured knowledge entries: bite-sized persistent context ("this repo uses Tailwind", "API responds with XML")
- Autogenerated codebase index showing where everything lives and what each part does
- Knowledge base per repo that can be edited manually or Devin suggests updates
- Recalls relevant context at every step during multi-file refactoring

**Limitations**:
- Does NOT maintain long-term memory across sessions (as of mid-2025)
- Context reasoning bounded by what fits in context window during session

**Recent Features**:
- Session management: create child sessions with structured output schemas
- Search/filter past sessions by tags, playbook, origin, time range
- Full search across shell, file, browser, git, and MCP activity

---

### 4. OpenAI Codex (API/Dashboard)

**Storage**: Structured context snapshots within session history
**Implementation**: Context compaction with state preservation

Sources:
- [Compaction | OpenAI API](https://developers.openai.com/api/docs/guides/compaction)
- [Context Engineering - Short-Term Memory Management with Sessions](https://developers.openai.com/cookbook/examples/agents_sdk/session_memory)
- [GitHub Issues - Compaction impacts](https://github.com/openai/codex/discussions/5799)

**Key Features**:
- Automatic context compaction when approaching token limits
- Lightweight state receipts preserved inside saved history ("what files looked like after a step")
- Compaction snapshots allow more reliable resume/fork after compaction
- Snapshots not shown as chat messages; don't expand model memory themselves

**Known Challenges**:
- Full history replaced with single bridge containing user prompts + summary
- Confirmations ("Bug X is fixed") vanish after compaction
- After 2-3 compactions, all reasoning and context from earlier compactions lost
- Race conditions and token usage inefficiency during compaction

---

### 5. Manus (AI Agent Framework)

**Storage**: File-based memory (task_plan.md, notes.md, deliverable files)
**Implementation**: "Memory as Documentation" philosophy using file system as external memory

Sources:
- [From Manus to MemU: Why Memory Is Becoming the Defining Layer of the Agent Era](https://medium.com/@memU_ai/from-manus-to-memu-why-memory-is-becoming-the-defining-layer-of-the-agent-era-9fd2f7c43800)
- [AI Agent Memory Management - When Markdown Files Are All You Need?](https://dev.to/imaginex/ai-agent-memory-management-when-markdown-files-are-all-you-need-5ekk)
- [Manus AI Completes 50-Step Tasks Autonomously](https://memu.pro/blog/manus-ai-autonomous-agent-memory)
- [Why Multi-Agent Systems Need Memory Engineering](https://www.mongodb.com/company/blog/technical/why-multi-agent-systems-need-memory-engineering)
- [Manus: Context Engineering Strategies for Production AI Agents](https://www.zenml.io/llmops-database/context-engineering-strategies-for-production-ai-agents)
- [Context Engineering for AI Agents: Lessons from Building Manus](https://manus.im/blog/Context-Engineering-for-AI-Agents-Lessons-from-Building-Manus)

**Key Features**:
- Three-file memory pattern: task_plan.md (goals/progress), notes.md (research), deliverable files
- File system treated as unlimited, persistent context
- Model learns to write to/read from files on demand as externalized memory
- Deliberate task recitation via continuously updated todo.md files
- Context Window Manager for selective memory in hierarchical multi-agent systems

**Architecture**:
- Deep chains of agents (up to 5 layers) without memory bloat
- Average input-to-output token ratio ~100:1
- KV-cache leveraging for identical prefixes (reduces time-to-first-token and cost)

---

### 6. Windsurf / Codeium

**Storage**: Memories + Rules system (editable in Customizations panel)
**Implementation**: Auto-generated + manually defined context

Sources:
- [Understanding Windsurf's Memories System for Persistent Context](https://www.arsturn.com/blog/understanding-windsurf-memories-system-persistent-context)
- [Cascade Memories - Windsurf Docs](https://docs.windsurf.com/windsurf/cascade/memories)
- [Context Aware Everything | Windsurf](https://windsurf.com/context)
- [GitHub - justinclift/windsurf_memory_server_v2: SQLite-based memory server](https://github.com/justinclift/windsurf_memory_server_v2)

**Key Features**:
- Auto-generation: Cascade automatically generates memories when encountering useful context
- Toggle: Auto-Generate Memories setting enables autonomous memory creation
- Rules system: Manually defined system-level, workspace-level, and global-level rules
- Multi-layered context: System rules merged with workspace and global rules
- Management: Via Customizations icon (top right) or Windsurf settings

**Persistent Context**:
- Cascade remembers coding patterns, project structure, preferred frameworks
- Carries over across sessions
- Rules provide organizational baseline while permitting project-specific customizations

---

### 7. Amazon Q Developer

**Storage**: Memory bank (auto-generated MD files) + workspace context + persistent conversations
**Implementation**: Hybrid (semantic indexing + persistent chat history)

Sources:
- [Generating a memory bank for Amazon Q chat](https://docs.aws.amazon.com/amazonq/latest/qdeveloper-ug/context-memory-bank.html)
- [Adding workspace context to Amazon Q Developer chat in the IDE](https://docs.aws.amazon.com/amazonq/latest/qdeveloper-ug/workspace-context.html)
- [AWS announces workspace context awareness for Amazon Q Developer chat](https://aws.amazon.com/blogs/devops/aws-announces-workspace-context-awareness-for-amazon-q-developer-chat/)
- [Chat history compaction in Amazon Q Developer](https://docs.aws.amazon.com/amazonq/latest/qdeveloper-ug/ide-chat-history-compaction.html)

**Memory Bank Files** (auto-generated under .amazonq/rules):
- product.md: Project overview and capabilities
- structure.md: Architecture, folder organization, key components
- tech.md: Technology stack, frameworks, dependencies, coding standards
- guidelines.md: Development standards and patterns

**Context Management**:
- @workspace annotation for automatic relevant code chunk inclusion
- Local indexing of workspace repository (filters out binaries, .gitignore files)
- Conversation persistence across IDE sessions
- Chat history compaction: preserves essential info while reducing context

---

### 8. Google Jules

**Storage**: Repository-level memory system with preference tracking
**Implementation**: Task-specific learning with session improvements

Sources:
- [Google's Jules AI Coding Assistant Set to Become More Autonomous](https://opentools.ai/news/googles-jules-ai-coding-assistant-set-to-become-more-autonomous-with-game-changing-update)
- [Google Jules Tutorial: Real Examples & Implementation](https://www.codecademy.com/article/google-jules)
- [Jules gains memory!](https://jules.google/docs/changelog/2025-09-30)
- [Google Jules: A Guide With 3 Practical Examples](https://www.datacamp.com/tutorial/google-jules)
- [New ways to build with Jules, our AI coding agent](https://blog.google/innovation-and-ai/models-and-research/google-labs/jules-tools-jules-api/)

**Key Features**:
- Memory learns from preferences, nudges, corrections during tasks
- Preference application: Next time running same/similar task in repo, Jules references memory
- Automatic application to future tasks with less guidance
- Configuration: Toggle memory on/off per repo in settings under "Knowledge"
- Minimizes repetitive adjustments, ensures consistency across projects

**Session Memory**:
- Environment variable support
- Improved memory carry-through during sessions
- Critic agent re-engagement more reliable after replanning
- Maintains focus during longer tasks

---

### 9. Augment Code

**Storage**: Semantic embeddings + persistent memory (curated by user)
**Implementation**: Deep code understanding + agent memory review

Sources:
- [Agent Memory Review— curate what your agent remembers](https://www.augmentcode.com/changelog/memory-review)
- [How we built Memory Review](https://www.augmentcode.com/blog/how-we-built-memory-review)
- [Context Engineering: Enhancing Agentic Swarm Coding](https://www.augmentcode.com/guides/context-engineering-enhancing-agentic-swarm-coding-through-intent-environment-and-system-memory)
- [How Augment Code Solved the Large Codebase Problem](https://blog.codacy.com/ai-giants-how-augment-code-solved-the-large-codebase-problem/)
- [Context Engine MCP - Augment Docs](https://docs.augmentcode.com/context-services/mcp/overview)

**Memory Review System**:
- Surface every memory before saving
- User can approve, edit, or discard
- Nothing stored without sign-off
- Lives in chat panel for inline curation

**Context Engine** (semantic approach):
- Entire repository ingestion with semantic embeddings
- Millisecond-level sync with code changes
- Relationship awareness across files, repos, services, architectures
- Indexes commit history, codebase patterns, external sources (docs, tickets)
- Smart retrieval: only what matters, compressed without losing info

**Persistent Memory Layer**:
- Stores prior interactions, code snippets, diagnostic breadcrumbs
- Current with code, test suite, deployment pipeline
- Augment Agent: 200K context tokens, persistent memory, deep tool integrations

---

### 10. Goose (Block)

**Storage**: Session-based conversation with auto-compaction summaries
**Implementation**: Smart context management with threshold-based summarization

Sources:
- [Smart Context Management | goose](https://block.github.io/goose/docs/guides/sessions/smart-context-management/)
- [GitHub - block/goose: open source, extensible AI agent](https://github.com/block/goose)
- [GOOSE . The In-Depth Guide for Developers Craving Real CLI AI](https://medium.com/the-context-layer/goose-the-in-depth-guide-for-developers-craving-real-cli-ai-c3742d9d5dc0)

**Auto-Compaction**:
- Triggers at 80% token limit threshold (customizable via GOOSE_AUTO_COMPACT_THRESHOLD)
- Summarizes older conversation parts, preserving key information
- Reduces context size without losing critical reasoning
- Can be disabled (set to 0.0)

**Context Strategies**:
- Primary: Auto-summarization
- Desktop: Summarization only
- CLI supports: summarize, truncate, clear, prompt

**Manual Control**:
- /summarize command to proactively compress conversation history
- Maintains previous messages visibility (visible but only summary in active context)

---

## Part 3: Comparative Analysis

### Memory Storage Approaches

| Framework | Storage Type | Persistence | Format |
|-----------|--------------|-------------|--------|
| Claude Code | File-based | Permanent (workspace) | Markdown |
| Cursor | File-based | Permanent (rules) | Text/Markdown |
| Devin | File-based | Per-session (no cross-session) | Text/Structured |
| OpenAI Codex | Context snapshots | Session-only | Structured state |
| Manus | File-based | Per-task | Markdown files |
| Windsurf | Hybrid (rules + embeddings) | Permanent (workspace) | Rules/Vectors |
| Amazon Q | Hybrid (memory bank + index) | Permanent | Markdown + Vector index |
| Google Jules | Repository-level | Per-repo | Preference store |
| Augment Code | Semantic embeddings | Permanent | Embeddings + text |
| Goose | Session snapshots | Session-only | Compacted summaries |

### Memory Retrieval Mechanisms

**Keyword-based**:
- Cursor .cursorrules (simple injection)
- Claude Code MEMORY.md (file read)

**Semantic Search**:
- OpenClaw memory_search tool
- Augment Code Context Engine
- Amazon Q workspace indexing
- Windsurf with embeddings

**Heuristic/Rule-based**:
- Claude Code (smart update decisions)
- Manus (task recitation)
- Google Jules (preference learning)

**Compaction/Summarization**:
- OpenAI Codex
- Goose (auto-compaction)
- Amazon Q (chat history compaction)

### Memory Lifecycle Patterns

**Creation**:
- Automatic: Claude Code, Windsurf, Amazon Q
- Manual: Cursor, Manus, Augment Code (review)
- Implicit: Devin notes, Goose summaries

**Update/Evolution**:
- Smart/Selective: Claude Code (relevance heuristics)
- Append: Manus (todo.md, notes.md)
- Summarization: OpenAI Codex, Goose
- User-curated: Cursor, Augment Code

**Decay/Deletion**:
- Explicit: Manual file deletion (most)
- Automatic: Goose compaction (hidden from active context)
- Implicit: Devin per-session (no cross-session memory)
- No decay: OpenClaw, Claude Code (permanent unless manually deleted)

### Cross-Session Continuity

| Framework | Cross-Session | Mechanism | Limitations |
|-----------|--------------|-----------|------------|
| Claude Code | Yes | Project-level MEMORY.md | 25KB limit per session load |
| Cursor | Yes | .cursorrules injection | Static rules |
| Devin | No | Session-only context | Fresh start each session |
| OpenAI Codex | No | Sessions are isolated | Need new session for continuity |
| Manus | Per-task | Task plan persistence | Task-specific |
| Windsurf | Yes | Memories + Rules | User-configurable |
| Amazon Q | Yes | Memory bank + persistent chats | Conversation-aware index |
| Google Jules | Yes | Per-repo preferences | Repo-specific |
| Augment Code | Yes | 200K context + embeddings | Large codebase support |
| Goose | No (session-specific) | Snapshots within session | Manual /summarize |

---

## Part 4: Key Findings and Patterns

### [事实] Established Facts

1. **File-based systems dominate coding agents** (OpenClaw, Claude Code, Cursor, Manus, Amazon Q)
   - Markdown/text files as persistent state are standard practice
   - Agents learn to read/write files as memory operations

2. **Hybrid approaches emerging** (Windsurf, Amazon Q, Augment Code)
   - Semantic embeddings + rule-based context
   - Semantic search enables deeper codebase understanding

3. **Context compaction is necessary** (OpenAI Codex, Goose, Amazon Q)
   - All approaches struggle with context window limitations
   - Summarization/compaction trades fidelity for cost and latency

4. **No standard memory protocol**
   - Each framework implements memory differently
   - No interoperability between systems

### [推导] Deduced Patterns

1. **File system = Externalizable Working Memory**
   - Agents treat filesystem as auxiliary memory (Manus, Claude Code, OpenClaw)
   - Prevents losing context during context compaction

2. **Memory review needed for safety** (Augment Code)
   - User curation of agent-generated memory improves reliability
   - Prevents agents from "forgetting" important context or mis-recording

3. **Cross-session continuity requires explicit design**
   - Stateless LLMs need persistent storage + retrieval
   - Injection timing matters (per-request vs. per-session vs. on-demand)

4. **Semantic retrieval > keyword matching for code**
   - Augment Code, Windsurf, Amazon Q all use embeddings
   - Understands relationships, not just text match

### [假说] Hypotheses

1. **Memory bottleneck is UI/UX, not technology**
   - Claude Code, Cursor, Windsurf all face user confusion about what's remembered
   - Explicit memory review (like Augment Code) may become standard

2. **Markdown will remain the memory lingua franca for agents**
   - Self-documenting format
   - Human-readable and agent-writable
   - Version control friendly (Git)

3. **150-300KB sweet spot for effective agent memory**
   - Claude Code loads 25KB
   - Augment Code uses 200K context tokens
   - Manus uses multi-agent chains to stay within limits
   - Suggests ~200K is practical maximum for fast retrieval

4. **Memory decay policies will become more sophisticated**
   - Current systems: permanent or none
   - Future: age-based, relevance-based, or LRU-style decay

### [开放问题] Open Questions

1. **Can memory systems scale to 1M+ line codebases?**
   - Augment Code claims to handle large codebases
   - No public benchmarks comparing memory efficiency

2. **How to prevent memory corruption/hallucination?**
   - If agents write memory, how to verify accuracy?
   - Augment Code's review system is one answer, but manual

3. **Should memory be agent-specific or global?**
   - Multi-agent systems: do all agents share memory? (Manus supports both)
   - Privacy/isolation implications unexplored

4. **Memory transfer between frameworks?**
   - Can Claude Code's MEMORY.md be used in Cursor?
   - No standardization effort visible

5. **What's the optimal memory refresh rate?**
   - Static files (Cursor): zero overhead but stale
   - Auto-updated (Claude Code, Windsurf): freshness but overhead
   - Optimal frequency unknown

---

## Part 5: OpenClaw's Unique Contributions

### Relationship to Memory/Isolation

**Memory Innovation**:
- Pre-compaction memory flush: explicitly writes durable memory before aggressive context compression
- Two-layer structure (daily + curated): separates ephemeral from permanent
- Semantic recall tools (memory_search): not just file reads but intelligent retrieval

**Isolation Innovation** (related to memory safety):
- Session isolation per channel prevents context leakage
- Docker sandboxing protects memory operations
- Canvas isolation separates agent-writable content from control plane
- Plugin isolation prevents memory corruption from extensions

**Synthesis**:
OpenClaw combines file-based memory persistence with explicit isolation mechanisms. This is a strategic choice: because agents in OpenClaw operate across multiple channels and sessions, memory must be:
1. Protected from cross-session contamination (session isolation)
2. Automatically persisted before context loss (pre-compaction flush)
3. Safely retrieved without running untrusted code (memory tools + plugin isolation)

### Comparison to Other Approaches

- vs. Claude Code: OpenClaw's pre-compaction flush is explicit; Claude Code relies on soft heuristics
- vs. Cursor: OpenClaw's isolation mechanisms are stronger (no file-level isolation in Cursor)
- vs. Devin: OpenClaw is cross-session; Devin restarts
- vs. Manus: Similar file-based approach, but OpenClaw adds tool sandboxing
- vs. Windsurf: OpenClaw's isolation is more thorough; Windsurf is more auto-focused

---

## References

### OpenClaw Core
- https://docs.openclaw.ai/concepts/memory
- https://velvetshark.com/openclaw-memory-masterclass
- https://milvus.io/blog/openclaw-formerly-clawdbot-moltbot-explained-a-complete-guide-to-the-autonomous-ai-agent.md
- https://www.roborhythms.com/openclaw-permanent-memory-setup/
- https://openclaw.substack.com/p/openclaw-architecture-part-3-memory
- https://nebius.com/blog/posts/openclaw-security
- https://ppaolo.substack.com/p/openclaw-system-architecture-overview
- https://eastondev.com/blog/en/posts/ai/20260205-openclaw-architecture-guide/
- https://github.com/Gen-Verse/OpenClaw-RL
- https://github.com/openclaw
- https://arxiv.org/html/2603.12644v1
- https://arxiv.org/html/2603.10387v1
- https://arxiv.org/abs/2603.10165

### Agent Frameworks
- https://code.claude.com/docs/en/memory
- https://medium.com/@joe.njenga/anthropic-just-added-auto-memory-to-claude-code-memory-md-i-tested-it-0ab8422754d2
- https://claudefa.st/blog/guide/mechanics/auto-memory
- https://dev.to/pockit_tools/mastering-cursor-rules-the-ultimate-guide-to-cursorrules-and-memory-alm
- https://medium.com/codetodeploy/advanced-cursor-use-the-memory-bank-to-eliminate-hallucination-affd3fbeefa3
- https://techpoint.africa/guide/devin-ai-review/
- https://docs.devin.ai/release-notes/overview/
- https://cognition.ai/blog/devin-annual-performance-review-2025/
- https://developers.openai.com/api/docs/guides/compaction
- https://developers.openai.com/cookbook/examples/agents_sdk/session_memory
- https://medium.com/@memU_ai/from-manus-to-memu-why-memory-is-becoming-the-defining-layer-of-the-agent-era-9fd2f7c43800
- https://dev.to/imaginex/ai-agent-memory-management-when-markdown-files-are-all-you-need-5ekk
- https://manus.im/blog/Context-Engineering-for-AI-Agents-Lessons-from-Building-Manus
- https://www.arsturn.com/blog/understanding-windsurf-memories-system-persistent-context
- https://docs.windsurf.com/windsurf/cascade/memories
- https://docs.aws.amazon.com/amazonq/latest/qdeveloper-ug/context-memory-bank.html
- https://aws.amazon.com/blogs/devops/aws-announces-workspace-context-awareness-for-amazon-q-developer-chat/
- https://docs.aws.amazon.com/amazonq/latest/qdeveloper-ug/ide-chat-history-compaction.html
- https://jules.google/docs/changelog/2025-09-30
- https://www.augmentcode.com/changelog/memory-review
- https://www.augmentcode.com/blog/how-we-built-memory-review
- https://www.augmentcode.com/guides/context-engineering-enhancing-agentic-swarm-coding-through-intent-environment-and-system-memory
- https://block.github.io/goose/docs/guides/sessions/smart-context-management/
- https://github.com/block/goose

### Comparative/Meta Research
- https://machinelearningmastery.com/the-6-best-ai-agent-memory-frameworks-you-should-try-in-2026/
- https://mem0.ai/blog/agentic-frameworks-ai-agents
- https://thenewstack.io/memory-for-ai-agents-a-new-paradigm-of-context-engineering/
- https://arxiv.org/abs/2512.13564
- https://github.com/Shichun-Liu/Agent-Memory-Paper-List
- https://vectorize.io/articles/best-ai-agent-memory-systems
- https://www.letta.com/blog/benchmarking-ai-agent-memory
