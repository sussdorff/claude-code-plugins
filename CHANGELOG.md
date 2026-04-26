# Changelog

All notable changes to the claude-code-plugins marketplace are documented here.

## [Unreleased]

### Features

- **session-close**: Add cliff.toml and --push-gate flag([8d8e374](https://github.com/sussdorff/claude-code-plugins/commit/8d8e3745597476c402700cfa274c3d07a8549029))
## [2026.04.138] - 2026-04-26

### Bug Fixes

- **session-close**: Push gate, no-stash rule, gitignore transient files([0b8151a](https://github.com/sussdorff/claude-code-plugins/commit/0b8151a7406ed7e9d9b72d4640c34bac8b76c14f))
- **beads**: PRIME.md example uses task not feature to avoid type inflation([9287925](https://github.com/sussdorff/claude-code-plugins/commit/92879255edd4c3b5d748ab0d4a34482530108acd))

### Documentation

- Update CHANGELOG.md for push gate and session-close fixes([933b904](https://github.com/sussdorff/claude-code-plugins/commit/933b904d33a47cd7817dd18505e94efbb9fc28a4))

### Features

- **session-close**: Push gate defers to next run when CI busy (default)([7f3d937](https://github.com/sussdorff/claude-code-plugins/commit/7f3d937f067f8f1cbe3d141ffd62da69f5a6d605))
## [2026.04.137] - 2026-04-26

### Documentation

- **CCP-vh2w**: Add spec for weekly-prompt-kit-review skill v1.1([db927bc](https://github.com/sussdorff/claude-code-plugins/commit/db927bce9e77a2c1d6becae66c64db3f18f1a9d0))
## [2026.04.136] - 2026-04-26

### Documentation

- **adr**: ADR-0004 — disable Claude Code sandbox for single-user dev([71b3140](https://github.com/sussdorff/claude-code-plugins/commit/71b3140d90b9156d51a2e6a50ffd3ff089cee332))
## [2026.04.134] - 2026-04-26

### Merge

- Worktree-bead-CCP-r1pa([fdf2fac](https://github.com/sussdorff/claude-code-plugins/commit/fdf2face7fff5429ee21de6cc896ba42c251c679))
## [2026.04.133] - 2026-04-26

### Bug Fixes

- **CCP-db1**: Address review findings iteration 1([0da5f6d](https://github.com/sussdorff/claude-code-plugins/commit/0da5f6d75f6b2e85f1de5528e5f9c382a3ad3b27))
- **CCP-db1**: Address codex adversarial findings([e8c9943](https://github.com/sussdorff/claude-code-plugins/commit/e8c9943ecdc51999e4c6246e951ee150f245237b))
- **CCP-r1pa**: Address review findings iteration 1([325d66d](https://github.com/sussdorff/claude-code-plugins/commit/325d66de59e8b480ae1c35f5142b1a52de289f35))
- **CCP-r1pa**: Address codex adversarial findings([942fc3a](https://github.com/sussdorff/claude-code-plugins/commit/942fc3a84e30ea1dcf4f04859089e5f042fe0c9b))

### Documentation

- **CCP-db1**: Update sample output + SKILL.md for v1.1 sections([0ac60f7](https://github.com/sussdorff/claude-code-plugins/commit/0ac60f7936ef557ac27edfa69c5e6d578265cc81))
- **CCP-db1**: Update data-sources.md with v1.1 section coverage([6418530](https://github.com/sussdorff/claude-code-plugins/commit/64185301aa05a3e306b5f8e2a43355c371388da7))
- **CCP-db1**: Add changelog entry for v1.1 sections([25d990d](https://github.com/sussdorff/claude-code-plugins/commit/25d990d27e30e98f65b044b7391d02f60df456d3))

### Features

- **CCP-db1**: Green — add Entscheidungsbedarf + Drift-und-Rework-Signale sections (v1.1)([9d5eacd](https://github.com/sussdorff/claude-code-plugins/commit/9d5eacd538c94eb7cea7a4181c4ac6ba88ca39dc))
- **CCP-r1pa**: Add Antman-style behavioral contract sections to spec-developer([50676f0](https://github.com/sussdorff/claude-code-plugins/commit/50676f0cc7883de8b005e15d3fbf88d301622271))

### Testing

- **CCP-db1**: Red — add failing tests for Entscheidungsbedarf + Drift & Rework sections([b8f230a](https://github.com/sussdorff/claude-code-plugins/commit/b8f230ad00ead1c6a816cb8539825fb87e276748))

### Merge

- Worktree-bead-CCP-cc7([a8a6418](https://github.com/sussdorff/claude-code-plugins/commit/a8a64181b6ab3f510ec9273ac2aabd723f102aae))

### Security

- **CCP-cc7**: Add permissionMode:ask to 4 high-risk agents in claude-code-plugins([c664fb8](https://github.com/sussdorff/claude-code-plugins/commit/c664fb81bd2a1d30382b9397a4132fcad34feeb6))
## [2026.04.132] - 2026-04-26

### Merge

- Worktree-bead-CCP-gtue([0680c45](https://github.com/sussdorff/claude-code-plugins/commit/0680c4559afad8364596e3eb62da26c6bea66e34))
## [2026.04.131] - 2026-04-26

### Bug Fixes

- **CCP-gtue**: Isolate brief_exists tests from real home directory([4857251](https://github.com/sussdorff/claude-code-plugins/commit/48572511a9f22ffb42018f7db30670dc779ef4ef))
- **CCP-sext**: Move open-brain-http-client standard to .claude/standards/ for inject-standards compatibility([00b28ef](https://github.com/sussdorff/claude-code-plugins/commit/00b28efb084ebbaa0eb5615873a6fa7c26f1116e))

### Documentation

- **CCP-sext**: Add ADR-0003 + standards ref for open-brain REST vs MCP decision tree([d27ceed](https://github.com/sussdorff/claude-code-plugins/commit/d27ceed4eaa033fd03394748df1e13190bb30e33))

### Refactoring

- **CCP-gtue**: Move daily-brief disk path to ~/.claude/projects/<slug>/daily-briefs/([58b059a](https://github.com/sussdorff/claude-code-plugins/commit/58b059a5e7175c4abf99c2b1c6bc6c5c5706bdcf))

### Merge

- Worktree-bead-CCP-sext([005d29c](https://github.com/sussdorff/claude-code-plugins/commit/005d29cbd527416a53e71f02d4d818b62f959f30))
## [2026.04.130] - 2026-04-25

### Merge

- Worktree-bead-CCP-glnq([12cc723](https://github.com/sussdorff/claude-code-plugins/commit/12cc7235c6d2f7cb7fda32d6bdc7d8e852e8de24))
## [2026.04.128] - 2026-04-25

### Bug Fixes

- **CCP-glnq**: Address review findings iteration 1([69644f7](https://github.com/sussdorff/claude-code-plugins/commit/69644f7589ca501c7285069b94e54c9af0a51abd))
- **CCP-glnq**: Address codex adversarial findings([0a163c5](https://github.com/sussdorff/claude-code-plugins/commit/0a163c5e6a739c7973541bf4f883e7459434bb30))
- **CCP-glnq**: Address auto-fixable verification disputes([ffccedc](https://github.com/sussdorff/claude-code-plugins/commit/ffccedce1d2e37c43d53728d49684da0c4ebb2e6))
- **CCP-glnq**: Raise integration test timeout 240→480s, sync codex skills([665efe6](https://github.com/sussdorff/claude-code-plugins/commit/665efe674b65e2236460b82810bbfd275a82a934))
- **CCP-glnq**: Translate German warning string to English (constraint compliance)([52816fe](https://github.com/sussdorff/claude-code-plugins/commit/52816fe3c9dde56fd3b8ba5a2478fb13a557cd16))
- **CCP-xtba**: Green — add duplicate-dispatch guard to wave-dispatch.py([fbb9a9a](https://github.com/sussdorff/claude-code-plugins/commit/fbb9a9af91f42bb4fa2b3d0aa850584e03065008))
- **CCP-xtba**: Green — add ownership check to phase-b-close-beads.sh([57d9fbc](https://github.com/sussdorff/claude-code-plugins/commit/57d9fbc9c5cac3c14baf3d7f258cdfda1ecc9caa))
- **CCP-xtba**: Address review findings iteration 1([187ff8c](https://github.com/sussdorff/claude-code-plugins/commit/187ff8cfd7f86b1f9fe9876ea18dba1d53f49902))
- **CCP-xtba**: Address codex adversarial findings([f66587f](https://github.com/sussdorff/claude-code-plugins/commit/f66587fad7bd671ecad4cdd2d4a082be0a2166f0))
- **CCP-xtba**: Add duplicate-dispatch guard and session-close ownership check([fa8a676](https://github.com/sussdorff/claude-code-plugins/commit/fa8a6761cf8712b7e59488caabf415fa28251933))
- **CCP-cp3**: Kill process group on timeout to unblock stdout pipe([3e1836d](https://github.com/sussdorff/claude-code-plugins/commit/3e1836def4c02c3f59d242ec84635a6535a3e08e))

### Features

- **CCP-glnq**: Green — open-brain as system-of-record (v1.5)([032db72](https://github.com/sussdorff/claude-code-plugins/commit/032db72f924914e8a227d1e6c8d617bca534bcf9))
- **CCP-glnq**: Green — migration script, ADR-0002, SKILL.md update([2bff0c9](https://github.com/sussdorff/claude-code-plugins/commit/2bff0c9b10339dcccc96df71d9923b32fa8e3b28))

### Miscellaneous

- **CCP-cp3**: Update bead state in issues.jsonl([213ff39](https://github.com/sussdorff/claude-code-plugins/commit/213ff3945b4e526ca8eef2516bb3de388be4d68b))

### Testing

- **CCP-glnq**: Red — AK1/2/3/6/7/8 failing tests for OB SoR feature([6c52e9a](https://github.com/sussdorff/claude-code-plugins/commit/6c52e9af802ebf0f5c22dc02569e30cffc3b2018))
- **CCP-xtba**: Red — add already-running guard tests for wave dispatcher([dd48b8f](https://github.com/sussdorff/claude-code-plugins/commit/dd48b8fb5c8324a5b5d5a09e5e6caf48e00567b2))

### Merge

- Worktree-bead-CCP-cp3([8ac9232](https://github.com/sussdorff/claude-code-plugins/commit/8ac923246523990e3410812dec4214f5f396247d))
## [2026.04.127] - 2026-04-25

### Bug Fixes

- **CCP-zodj**: Call search tool once per type string, parse results from response dict([896bab1](https://github.com/sussdorff/claude-code-plugins/commit/896bab15548515d7130edfa424df6bb2b9c845b0))
- **CCP-zodj**: Inline make_config_path in SDK tests — tests/ has no __init__.py([1d0ce5e](https://github.com/sussdorff/claude-code-plugins/commit/1d0ce5e42c43d315e4a058349e89fccc4e3c266c))
- **CCP-zodj**: Address codex adversarial findings([cc3cb9e](https://github.com/sussdorff/claude-code-plugins/commit/cc3cb9eba437384a055897daabe99b968cce769b))

### Documentation

- **CCP-zodj**: Add ADR-0001 documenting mcp SDK over homegrown HTTP transport decision([686caa6](https://github.com/sussdorff/claude-code-plugins/commit/686caa68c42841d61c0686ea53d3eee69b84db0d))

### Features

- **CCP-zodj**: Replace homegrown httpx _OBClient with official mcp Python SDK([9e13af5](https://github.com/sussdorff/claude-code-plugins/commit/9e13af5b2c8941956561372fef9ad1c0a43de1b1))

### Miscellaneous

- **CCP-zodj**: Update changelog with mcp SDK migration entry([70dc5cd](https://github.com/sussdorff/claude-code-plugins/commit/70dc5cd68a9035c2bbf83c967b6c626d22343b91))

### Testing

- **CCP-zodj**: Red — SDK-based MCP client tests for query-sources and orchestrate-brief([656b5dc](https://github.com/sussdorff/claude-code-plugins/commit/656b5dc50d44fa78a35a18da736463904b323e71))
## [2026.04.126] - 2026-04-25

### Bug Fixes

- **CCP-sd9e**: Correct open-brain MCP URL path /mcp/mcp→/mcp + add Accept header([16367a3](https://github.com/sussdorff/claude-code-plugins/commit/16367a34e8ab3cdb4da6224ba6c228bd667772d7))

### Miscellaneous

- **CCP-sd9e**: Update changelog with open-brain MCP URL fix entry([5d9720a](https://github.com/sussdorff/claude-code-plugins/commit/5d9720ae0d4cc45a9fe081c23d25984228ef60fc))
## [2026.04.125] - 2026-04-25

### Bug Fixes

- **CCP-scw5**: Use x-api-key header instead of Authorization: Bearer in _OBClient([2934d63](https://github.com/sussdorff/claude-code-plugins/commit/2934d63e277bbbe9bb900fb436700e0d00f328c9))

### Miscellaneous

- **CCP-scw5**: Update changelog with auth header fix entry([9832519](https://github.com/sussdorff/claude-code-plugins/commit/983251906088fb6dcf52bc973893ff6899fb694f))

### Testing

- **CCP-scw5**: Red — auth header regression tests for x-api-key vs Bearer([eeec8c4](https://github.com/sussdorff/claude-code-plugins/commit/eeec8c42edc0a6035392db6f613dbad76f3deb49))
## [2026.04.124] - 2026-04-25

### Miscellaneous

- Update CHANGELOG.md after CCP-6n3 merge([9970f9f](https://github.com/sussdorff/claude-code-plugins/commit/9970f9f670ff207039fe1f421fd84d54a82595e7))
- Merge origin/main into worktree-bead-CCP-i8g([71b4e93](https://github.com/sussdorff/claude-code-plugins/commit/71b4e93b4de23983faa9626834fe07787747b6a3))
- **CCP-i8g**: Update beads state before session close([180d1ac](https://github.com/sussdorff/claude-code-plugins/commit/180d1ac84deba7f21d26fb350df8e6842c4b4903))

### Merge

- Worktree-bead-CCP-i8g([899e554](https://github.com/sussdorff/claude-code-plugins/commit/899e55489e20a3623a34188161d2bee988994efb))
## [2026.04.123] - 2026-04-25

### Bug Fixes

- **CCP-i8g**: Address review findings iteration 1([e6a47ab](https://github.com/sussdorff/claude-code-plugins/commit/e6a47ab8d8826ce14220816a3e6703c6b408a218))
- **CCP-i8g**: Address codex adversarial findings — remove module-level config import, use subprocess([9207810](https://github.com/sussdorff/claude-code-plugins/commit/9207810ee41160f48d1e47108863738dc90b5338))
- **CCP-6n3**: Address review findings iteration 1([cc6293f](https://github.com/sussdorff/claude-code-plugins/commit/cc6293f6c773fea5676bff284419bdfdec64e8c2))
- **CCP-6n3**: Address codex adversarial findings([118c51a](https://github.com/sussdorff/claude-code-plugins/commit/118c51a2bc9170bba649b8afc5d11e2837830110))

### Features

- **CCP-i8g**: Green — integration test, reference docs, sample output, SKILL.md links([46b5462](https://github.com/sussdorff/claude-code-plugins/commit/46b5462e17f66dc7e88deb3db02815d52c7882c3))
- **CCP-6n3**: Green — discover-projects + --all-active mode([a883906](https://github.com/sussdorff/claude-code-plugins/commit/a883906f299ca2e22ff241231e609be8d5689154))

### Miscellaneous

- **CCP-i8g**: Update changelog with integration test entry([12a855e](https://github.com/sussdorff/claude-code-plugins/commit/12a855e9e9f38b58daeeb45c57a137192da7a548))
- **CCP-6n3**: Update beads state after session close([df14404](https://github.com/sussdorff/claude-code-plugins/commit/df144047b921c8e2e4fde1cc5afc1b5386a9b6f3))

### Testing

- **CCP-i8g**: Red — integration test for daily-brief --since=7d across all 4 projects([9823d4b](https://github.com/sussdorff/claude-code-plugins/commit/9823d4bf7fdaa8835503101cd56eeaeada2ba766))
- **CCP-6n3**: Red — discover-projects + --all-active TDD tests([65dddee](https://github.com/sussdorff/claude-code-plugins/commit/65dddeed1e0566038045cfa27fa4bff693c19be0))

### Merge

- Worktree-bead-CCP-6n3([e3dc4c0](https://github.com/sussdorff/claude-code-plugins/commit/e3dc4c0afda862ff33e9b7fcabccd1646f162390))
## [2026.04.122] - 2026-04-25

### Miscellaneous

- Merge origin/main into worktree-bead-CCP-yosw([491c7ec](https://github.com/sussdorff/claude-code-plugins/commit/491c7ec2b0afe834ac1a027c1f271b71efa5ff36))

### Merge

- Worktree-bead-CCP-yosw([6196e52](https://github.com/sussdorff/claude-code-plugins/commit/6196e527d20a563f9d227d76939c069ee9c15969))
## [2026.04.121] - 2026-04-25

### Bug Fixes

- **CCP-yosw**: Green — read ob credentials from ~/.open-brain/config.json([a124807](https://github.com/sussdorff/claude-code-plugins/commit/a1248071169066c53a5adf610d8be77a0687fb5c))
- **CCP-yosw**: Address review findings iteration 1([b1c6544](https://github.com/sussdorff/claude-code-plugins/commit/b1c654469f6378850b1a49f93e2863dd2058f628))
- **CCP-yosw**: Address codex adversarial findings — URL resolution independent of token source([9e918f6](https://github.com/sussdorff/claude-code-plugins/commit/9e918f682c0469e7406e956fcc2b623a74dd4250))
- **CCP-0qzc**: Replace *.db detection with config.yaml/issues.jsonl, scope bd via cwd([095695e](https://github.com/sussdorff/claude-code-plugins/commit/095695ed2acd577dd199cff4f5759f786ab276be))

### Testing

- **CCP-yosw**: Red — _build_ob_client and _save_to_open_brain config.json resolution([208ad4f](https://github.com/sussdorff/claude-code-plugins/commit/208ad4f8f070d23dca1632b32f8354fac7930f8d))

### Merge

- Worktree-bead-CCP-0qzc([b71545e](https://github.com/sussdorff/claude-code-plugins/commit/b71545e04ae337b17bf4df464a23de6fb0b10480))
## [2026.04.120] - 2026-04-24

### Bug Fixes

- **CCP-51k**: Fix render-brief.py persist bug — brief_exists check + correct config_path usage in brief_path()([0dccb7a](https://github.com/sussdorff/claude-code-plugins/commit/0dccb7ae0b7e00093034ca3cd7c4c10fb2bfe4d0))
- **CCP-51k**: Fix open-brain persistence in range mode — track new dates before render subprocess runs([d09f5de](https://github.com/sussdorff/claude-code-plugins/commit/d09f5de0ef92193f4d29f4826580789bb65e5ef8))
- **CCP-51k**: Address codex adversarial findings — save per-day brief content to open-brain (not rollup)([3b366d1](https://github.com/sussdorff/claude-code-plugins/commit/3b366d157eabd1a56f92f9ceb7fba9e323ed0b69))
- **CCP-51k**: Revert overly complex range backfill — keep clean backfill via brief_exists in render_single_day([9b51cc5](https://github.com/sussdorff/claude-code-plugins/commit/9b51cc550656571ae0eef05de32f92157ad6201a))

### Features

- **CCP-51k**: Green — orchestrate-brief.py CLI orchestration (backfill, open-brain, range, all CLI args)([23ff0b1](https://github.com/sussdorff/claude-code-plugins/commit/23ff0b1d4511daf7dc0c19a77cb4b4a801e85360))
- **CCP-51k**: Green — update SKILL.md with triggers, orchestration CLI docs, validate-skill.py clean([43e50a7](https://github.com/sussdorff/claude-code-plugins/commit/43e50a7c0aa8903ebe330484442249ccd97c2b3a))

### Miscellaneous

- **CCP-51k**: Update changelog with orchestrate-brief.py entry([5c921e6](https://github.com/sussdorff/claude-code-plugins/commit/5c921e65ca806caaad9e739dc18dd05820663d7a))

### Testing

- **CCP-51k**: Red — orchestrate-brief.py TDD tests (CLI args, backfill, open-brain, orchestration)([9f4ca02](https://github.com/sussdorff/claude-code-plugins/commit/9f4ca02bb7f8d7b1e9aa21a40aa324a1df76866e))
## [2026.04.119] - 2026-04-24

### Bug Fixes

- **CCP-lx2**: Address review findings — word-boundary matching for 'now' keyword, German grammar fixes in render-brief([e853044](https://github.com/sussdorff/claude-code-plugins/commit/e85304474bcac0bc79a7aca029a105769ffa17fe))
- **CCP-lx2**: Address codex adversarial findings — persist flag in range mode, detailed prose expansion, neutral temporal language, management anchor visibility([3e7dd43](https://github.com/sussdorff/claude-code-plugins/commit/3e7dd4356743654821092e70d608bbb917fb3c73))
- **CCP-lx2**: Include warnings-only days in executive summary (warnings are management anchors)([77ff497](https://github.com/sussdorff/claude-code-plugins/commit/77ff4973c1bdea05f9d4dcfe2ee0cff95ceaba31))

### Documentation

- Update CHANGELOG.md for v2026.04.118([ac4b4fc](https://github.com/sussdorff/claude-code-plugins/commit/ac4b4fc9972788a40b7c85f11e16abe50d0ac232))

### Features

- **CCP-lx2**: Green — document capability-extractor.py and render-brief.py in SKILL.md([b9c7ec0](https://github.com/sussdorff/claude-code-plugins/commit/b9c7ec0ebfccfcaaeccee299f982cc13bf0de96d))

### Miscellaneous

- **CCP-lx2**: Update changelog with capability-extractor + render-brief entry([179048c](https://github.com/sussdorff/claude-code-plugins/commit/179048c342576ed1efbddc13c8dde102f76bd259))

### Testing

- **CCP-lx2**: Red/green — capability-extractor.py signal detection tests (35 tests)([f660259](https://github.com/sussdorff/claude-code-plugins/commit/f6602598c1134dace379ce88c2e213e6fdf41aa6))
- **CCP-lx2**: Red/green — render-brief.py v1.0 section renderer tests (42 tests)([1642f14](https://github.com/sussdorff/claude-code-plugins/commit/1642f14b7535b96037d4a71e142d8c2764032edc))
## [2026.04.118] - 2026-04-24

### Miscellaneous

- **CCP-top**: Update bead state and changelog for session close([90170b3](https://github.com/sussdorff/claude-code-plugins/commit/90170b384c3851102489cba09babd3671520b156))

### Merge

- Worktree-bead-CCP-top([8b6bbdc](https://github.com/sussdorff/claude-code-plugins/commit/8b6bbdc759a881c2cfd664ee5eb1ed42926a450a))
## [2026.04.117] - 2026-04-24

### Merge

- Worktree-bead-CCP-die([002804a](https://github.com/sussdorff/claude-code-plugins/commit/002804aead0d64a806f7ada124aa82e595daaae2))
## [2026.04.116] - 2026-04-24

### Bug Fixes

- **CCP-top**: Address review findings iteration 1([adf482b](https://github.com/sussdorff/claude-code-plugins/commit/adf482b0acfe5492ac4e9b83df5097afd654032b))
- **CCP-top**: Address codex adversarial findings([6dc3bcd](https://github.com/sussdorff/claude-code-plugins/commit/6dc3bcd46ba73e97a84977cf48a9563917e1596a))
- **CCP-top**: Address codex adversarial findings([90d6b90](https://github.com/sussdorff/claude-code-plugins/commit/90d6b90275e7b57b99b9ac2169302cbe59b1934b))
- **CCP-die**: Green — align inline threshold with prompt char budget([99d729f](https://github.com/sussdorff/claude-code-plugins/commit/99d729ffdfef36856a2ca5e4709fad7950a49383))
- **CCP-die**: Address review findings iteration 1([13edc5c](https://github.com/sussdorff/claude-code-plugins/commit/13edc5c01e23ca6376a2915171d0e8deb5299afe))

### Documentation

- **CCP-top**: Add query-sources.py reference to daily-brief SKILL.md([ad045e7](https://github.com/sussdorff/claude-code-plugins/commit/ad045e755e87e0e94b82187e757775d0f489f6b3))

### Features

- **CCP-top**: Green — query-sources.py data aggregator for daily-brief([dc99aaa](https://github.com/sussdorff/claude-code-plugins/commit/dc99aaa819daa84998c8c5f9fc2a0648ffce0bdb))

### Miscellaneous

- **CCP-die**: Update bead state and changelog for session close([640bea7](https://github.com/sussdorff/claude-code-plugins/commit/640bea7b3f6102f6e3d61b8ef02a55686205846e))
- **CCP-die**: Update bead state and changelog for session close([d82cc1e](https://github.com/sussdorff/claude-code-plugins/commit/d82cc1e5a93afb7edc5ed6755f51a14969929808))

### Testing

- **CCP-top**: Red — query-sources tests and fixture config([578f453](https://github.com/sussdorff/claude-code-plugins/commit/578f4537eff8bda14deb2857a95211313827e746))
- **CCP-die**: Regression tests for codex-exec diff resolution([86cff08](https://github.com/sussdorff/claude-code-plugins/commit/86cff08b500d2e618ad22adfea8fdcd702b1d6b5))
- **CCP-die**: Red — large-diff fallback activates within prompt budget([1265b7f](https://github.com/sussdorff/claude-code-plugins/commit/1265b7f70b54392eb344cc4c0a3149c106bc3b56))

### Merge

- Worktree-bead-CCP-die([931232a](https://github.com/sussdorff/claude-code-plugins/commit/931232aec2dc41f62b6dc9dcbec9eb8057ff75d7))
## [2026.04.115] - 2026-04-24

### Miscellaneous

- **CCP-pof**: Update bead state and changelog for session close([35c0974](https://github.com/sussdorff/claude-code-plugins/commit/35c0974447f0553105a1dba288c5b1f24a44c837))

### Merge

- Worktree-bead-CCP-pof([f9a8edf](https://github.com/sussdorff/claude-code-plugins/commit/f9a8edfe66d6f48cb19b41e4a87af1b161a01644))
## [2026.04.114] - 2026-04-24

### Merge

- Worktree-bead-CCP-kww([477b24d](https://github.com/sussdorff/claude-code-plugins/commit/477b24dd0ee225f2f3fa3cf40e30fb08c177e06d))
## [2026.04.113] - 2026-04-24

### Bug Fixes

- **CCP-pof**: Remove trailing whitespace in uat-fixtures.md([6bb21a9](https://github.com/sussdorff/claude-code-plugins/commit/6bb21a993a3fedd6246f9a75a78bfceada3a7998))
- **CCP-kww**: Fix stray code fence in adr-location.md + correct version example in SKILL.md([57f3dd8](https://github.com/sussdorff/claude-code-plugins/commit/57f3dd8cd46584fff8233ac1997535bc9455773f))

### Documentation

- **CCP-pof**: UAT audit, fixture strategy, and standards([e641ed0](https://github.com/sussdorff/claude-code-plugins/commit/e641ed03063a06f6a950845c62ace1e45528026d))

### Features

- **CCP-kww**: Add /docs/adr/ scaffolding to project-setup + adr-location standard([6aa559c](https://github.com/sussdorff/claude-code-plugins/commit/6aa559c2229b7b73bcb3dc47360add29997fe604))

### Miscellaneous

- **CCP-kww**: Update bead state for session close([b0dd9a6](https://github.com/sussdorff/claude-code-plugins/commit/b0dd9a6058b649602ad70a099f4790a240aa93a7))
- **CCP-jtx**: Update bead state for session close([744add1](https://github.com/sussdorff/claude-code-plugins/commit/744add1f0461f125a919f6e2630e7b117a1490c4))

### Refactoring

- **CCP-jtx**: Remove orphaned WaveDispatcher.cmux_identify() method([1b90ff6](https://github.com/sussdorff/claude-code-plugins/commit/1b90ff6d434354ea5204cd91dcaeb2c8bb2b412f))

### Merge

- Worktree-bead-CCP-jtx([e95382b](https://github.com/sussdorff/claude-code-plugins/commit/e95382b4fb4b9b6e89806eee2deb73b9317ca675))
## [2026.04.112] - 2026-04-24

### Miscellaneous

- **CCP-ijh**: Merge main into feature branch (resolve test_daily_brief_config.py conflict)([3eee5f3](https://github.com/sussdorff/claude-code-plugins/commit/3eee5f3fbbbdda2039307451c5b9e19901457501))

### Merge

- Worktree-bead-CCP-ijh([898ad15](https://github.com/sussdorff/claude-code-plugins/commit/898ad159d2bd70490f4aed3a2f1d3bd0a2af1ac0))
## [2026.04.111] - 2026-04-24

### Bug Fixes

- **CCP-ijh**: Remove unused 'field' import from dataclasses([736d3e9](https://github.com/sussdorff/claude-code-plugins/commit/736d3e9369d7a9b0763bbcb2de243128e953f7be))
- **CCP-ijh**: Add SKILL.md to daily-brief skill directory([4f5e274](https://github.com/sussdorff/claude-code-plugins/commit/4f5e274f5bd85d97cf7f604624d1e6ef67879b79))
- **CCP-ijh**: Run sync-codex-skills to resolve TestUserScopedSync regressions([9a1d50c](https://github.com/sussdorff/claude-code-plugins/commit/9a1d50c77535218d64e2ee3143f7f9b715fe2857))
- **CCP-ijh**: Remove unused json import from test file([c585169](https://github.com/sussdorff/claude-code-plugins/commit/c585169862ef969e4e9826be7e5b1b94c2f49b6e))
- **CCP-b9d**: Use ${CLAUDE_PLUGIN_ROOT} for plugin script paths + add lint gate([8c54b14](https://github.com/sussdorff/claude-code-plugins/commit/8c54b14b3cd6ce88df25163e950d957ea5e71631))
- **CCP-ijh**: Remove unused 'field' import from dataclasses([8fe4d01](https://github.com/sussdorff/claude-code-plugins/commit/8fe4d01d8cecbb69ba108fa1bf22e0b60ba88350))

### CI/CD

- Bump actions to Node 24 (checkout@v5, setup-python@v6)([451953d](https://github.com/sussdorff/claude-code-plugins/commit/451953de7e66a57cd670612b78b1f8c8294be863))
- Re-trigger workflow on its own YAML changes([8cf871c](https://github.com/sussdorff/claude-code-plugins/commit/8cf871cbbbbafdb7bf95b5bd2cab1b0dffd4d277))

### Features

- **CCP-ijh**: Daily-brief config schema + per-project brief storage layout([0dcce81](https://github.com/sussdorff/claude-code-plugins/commit/0dcce81aac619bf2833c3812fe2ed5926647fd3c))
- **CCP-ijh**: Daily-brief config schema + per-project brief storage layout([31d4725](https://github.com/sussdorff/claude-code-plugins/commit/31d4725d79e68e5925d348def708ac85972346ff))

### Miscellaneous

- **CCP-ijh**: Update changelog with daily-brief config entry([686efb5](https://github.com/sussdorff/claude-code-plugins/commit/686efb5b59533592080764e1bf487d71caa4877e))
- **CCP-ijh**: Update bead state for session close([a9ee6db](https://github.com/sussdorff/claude-code-plugins/commit/a9ee6db996065d09df94a2748dea55cf9daa212c))
- Update changelog for session 2026-04-24([f128fe8](https://github.com/sussdorff/claude-code-plugins/commit/f128fe8f6e5afc1de950326c270ea7265a7f65c8))

### Testing

- **verification-provenance**: Update stale tests to match renumbered phases([162f6e4](https://github.com/sussdorff/claude-code-plugins/commit/162f6e41223fa02a224752e6e74d473b6d4c9a04))
## [2026.04.110] - 2026-04-23

### Bug Fixes

- **version.sh**: Stage plugin.json bumps in main repo, not worktree([53dc339](https://github.com/sussdorff/claude-code-plugins/commit/53dc3398089cc3563242c3cb0a180a3c150d0786))
- **wave-orchestrator**: Require --workspace and --base-pane explicitly([9d8b0dd](https://github.com/sussdorff/claude-code-plugins/commit/9d8b0dddb6c1a5a761ecf1fb2e9ee069b9734fa7))
## [2026.04.109] - 2026-04-23

### Miscellaneous

- Bump beads-workflow plugin.json to 2026.04.108([a84c4e3](https://github.com/sussdorff/claude-code-plugins/commit/a84c4e3eb9cc90d07a6170ae0d0f7eb234d3b6a4))
## [2026.04.108] - 2026-04-23

### Features

- **CCP-h8h**: Eliminate in-repo Codex mirrors — dev-repo principle([31d5c93](https://github.com/sussdorff/claude-code-plugins/commit/31d5c935957dc93944273421452ee55a19e65c8d))

### Miscellaneous

- **CCP-h8h**: Update changelog with dev-repo-principle entry([2e8077a](https://github.com/sussdorff/claude-code-plugins/commit/2e8077a5f1249194095d7fed51b523d77cf48e23))

### Testing

- **CCP-h8h**: Red — dev-repo-principle assertions (mirrors absent, sync user-only, arch doc)([88f71ca](https://github.com/sussdorff/claude-code-plugins/commit/88f71cac2688d787d35ec8b64178f9b914796d4f))

### Merge

- Worktree-bead-CCP-4h1([ea75009](https://github.com/sussdorff/claude-code-plugins/commit/ea7500917e2f5eb6f855e92e2e3060c009638411))
## [2026.04.107] - 2026-04-23

### Merge

- Bring in origin/main (first merge)([31e7fb6](https://github.com/sussdorff/claude-code-plugins/commit/31e7fb67ddbef09bed23accb2f3be1d7817314a4))
- Worktree-bead-CCP-tox([cc2739b](https://github.com/sussdorff/claude-code-plugins/commit/cc2739b13a0344dde6964cb553b6052656d90f59))
## [2026.04.106] - 2026-04-23

### Miscellaneous

- **CCP-9t5**: Session close — sync bead state after merge([234fa36](https://github.com/sussdorff/claude-code-plugins/commit/234fa36486134a65789da550dc2028f785983626))

### Merge

- Worktree-bead-CCP-9t5([8dcb607](https://github.com/sussdorff/claude-code-plugins/commit/8dcb607af0d6fc0e9715ee7927982f0e734594e4))
## [2026.04.105] - 2026-04-23

### Bug Fixes

- **CCP-4h1**: Address review findings iteration 1([c9691f4](https://github.com/sussdorff/claude-code-plugins/commit/c9691f4d3e896f8a11a593c170fdca746b2b1926))
- **CCP-tox**: Address review findings iteration 1([9f44a22](https://github.com/sussdorff/claude-code-plugins/commit/9f44a22709074c4367d1a055e593084dad3f5f36))
- **CCP-tox**: Address codex adversarial findings([c8309f5](https://github.com/sussdorff/claude-code-plugins/commit/c8309f5ca057c40dd5c3f252f8e51a86f5d5dc62))
- **CCP-9t5**: Deduplicate PROJECT sanitization in query-events.sh([45fd077](https://github.com/sussdorff/claude-code-plugins/commit/45fd0774a71ffb62001b12ca5d3f548140151422))
- **CCP-9t5**: Address codex adversarial findings in extracted scripts([359102f](https://github.com/sussdorff/claude-code-plugins/commit/359102fb1628b4d25756ff7601d818f3e725bad6))
- **CCP-a5d**: Fix stdin conflict in parse-cpanel-zone.sh and arg forwarding in piler-commands.sh([f182754](https://github.com/sussdorff/claude-code-plugins/commit/f18275463d388f50942590a6b4deadf21b1171a5))

### Documentation

- **CCP-4h1**: Update changelog for business skills refactoring([1c7d5a8](https://github.com/sussdorff/claude-code-plugins/commit/1c7d5a8bed654ca26b922a273f85e0e54bf300c2))

### Miscellaneous

- **CCP-4h1**: Sync bead state (issues.jsonl)([8f5ef3d](https://github.com/sussdorff/claude-code-plugins/commit/8f5ef3d4a82d843299702f6dbbf675c6b3ae600c))
- **CCP-4h1**: Sync bead state (issues.jsonl) #2([ee53489](https://github.com/sussdorff/claude-code-plugins/commit/ee53489e5fa9746fbda392fcf70afbc68ec8d7de))
- **CCP-tox**: Update changelog([40f0d01](https://github.com/sussdorff/claude-code-plugins/commit/40f0d01ad7a8238cdea679c53dee14edc4b48d9c))
- **CCP-tox**: Sync bead state (issues.jsonl)([857fa40](https://github.com/sussdorff/claude-code-plugins/commit/857fa406cc74afc8518e2d26bc7e6abb4ee33e75))

### Refactoring

- **CCP-4h1**: Extract inline code blocks from amazon skill to scripts/([3e03357](https://github.com/sussdorff/claude-code-plugins/commit/3e03357d260edab2085507bd39b8475526265d94))
- **CCP-4h1**: Extract inline code blocks from collmex-cli skill to scripts/([c4f4bcc](https://github.com/sussdorff/claude-code-plugins/commit/c4f4bcccb9ae42be4e1590fbda632a15688833af))
- **CCP-4h1**: Extract inline code blocks from google-invoice skill to scripts/([726e569](https://github.com/sussdorff/claude-code-plugins/commit/726e56911606cc3798635feb9fb34278f1bce1e6))
- **CCP-4h1**: Extract inline code blocks from mail-send skill to scripts/([9b3ee75](https://github.com/sussdorff/claude-code-plugins/commit/9b3ee752df7195624868ac2f58d177748d0fd093))
- **CCP-4h1**: Extract inline code blocks from mm-cli skill to scripts/([3de55f8](https://github.com/sussdorff/claude-code-plugins/commit/3de55f8cbcf4cccc2a34a53e621cf13aa01b96a5))
- **CCP-4h1**: Extract inline code blocks from op-credentials skill to scripts/([d83dec4](https://github.com/sussdorff/claude-code-plugins/commit/d83dec4f6d5500c17c9d155cbe4810987a4f07d2))
- **CCP-tox**: Extract codex JSONL parser to parse-codex-jsonl.py([38d4a05](https://github.com/sussdorff/claude-code-plugins/commit/38d4a05db40e43f83514ec57b6f70b40496a6ece))
- **CCP-tox**: Extract playwright-cli command docs to references/commands.md([2410e5f](https://github.com/sussdorff/claude-code-plugins/commit/2410e5ffec832b1b548b6f416f4727467b92dd29))
- **CCP-tox**: Extract vision-author inline code to scripts/([0642d76](https://github.com/sussdorff/claude-code-plugins/commit/0642d76044f8be58986fab26501c8ee8019db389))
- **CCP-9t5**: Extract inline code blocks to scripts (cmux, dolt, event-log)([4da464f](https://github.com/sussdorff/claude-code-plugins/commit/4da464fd991a42e9426c1d8f7fe99d1986bc0da6))
- **CCP-a5d**: Extract inline shell blocks to scripts in infra skills([efcf467](https://github.com/sussdorff/claude-code-plugins/commit/efcf4676af93273f1e18c30b472936a033bf4548))

### Merge

- Worktree-bead-CCP-a5d([8050aef](https://github.com/sussdorff/claude-code-plugins/commit/8050aef3c92ae9eb03873bd64dcd98c6a8f96e2c))
## [2026.04.103] - 2026-04-23

### Bug Fixes

- **codex-exec**: Bound large-diff review scope([b182ed5](https://github.com/sussdorff/claude-code-plugins/commit/b182ed52a8d0260c48abf05f14e435d86dd35d76))
- Sync plugin.json versions to 2026.04.102 and fix dry-run arg expansion in phase-b-ship([d8cb656](https://github.com/sussdorff/claude-code-plugins/commit/d8cb6561df6dd1130544510788fb355ed31bf19f))
- **CCP-8ha**: Resolve main repo root from worktree in version.sh([84b6532](https://github.com/sussdorff/claude-code-plugins/commit/84b65322f08cf40445875019e834ab38d91b948f))
- **CCP-zrp**: Fix SIGPIPE regression, remove misleading filter docs, fix scout mode resolution([23615fc](https://github.com/sussdorff/claude-code-plugins/commit/23615fc0304e5afb30ff3acf3b1153955354fdd6))
- **CCP-bjy**: Sync billing-reviewer Codex export after script extraction([20fef1f](https://github.com/sussdorff/claude-code-plugins/commit/20fef1fe2ebd67554fc6e75f7e13ebd908234db9))
- **CCP-nvs**: Capture surface ref dynamically in extracted cmux-browser scripts([9eada5c](https://github.com/sussdorff/claude-code-plugins/commit/9eada5c4886d56ad96632c6eb193e532e1b652d8))
- **CCP-d0q**: Resolve runtime errors in extracted scripts([6752902](https://github.com/sussdorff/claude-code-plugins/commit/6752902c96ee14b2edce39dd98f34716b9960917))

### Documentation

- Freeze wave-orchestrator feature work([f275898](https://github.com/sussdorff/claude-code-plugins/commit/f275898ff88c546af58a9bc1c0397b2c372a1954))
- Add gas city feasibility spike plan([c91d9f8](https://github.com/sussdorff/claude-code-plugins/commit/c91d9f83111d89e82a8993e562e176e1267b2653))

### Features

- **CCP-wyi**: Sync full skill fleet to codex([e4ed1f1](https://github.com/sussdorff/claude-code-plugins/commit/e4ed1f14f8d9cb0d58e533f55f5a952cdb6473c4))
- **CCP-wyi**: Complete codex parity and agent sync([a07b591](https://github.com/sussdorff/claude-code-plugins/commit/a07b5916b847b3249ae136394895354df1470607))

### Miscellaneous

- **CCP-0ho**: Add changelog entry and sync issues.jsonl([cedd0d8](https://github.com/sussdorff/claude-code-plugins/commit/cedd0d85fa2796594becadc35ff28b031609f831))
- **CCP-bjy**: Update bead state for session close([ede3a0e](https://github.com/sussdorff/claude-code-plugins/commit/ede3a0e2411c8a9fc40da2355835168d00da14bc))
- **CCP-nvs**: Update bead state for session close([1471b41](https://github.com/sussdorff/claude-code-plugins/commit/1471b41b2c7be0713ec400d161393188218e5c7f))
- Sync bead state before merge([34c2177](https://github.com/sussdorff/claude-code-plugins/commit/34c2177a82a06658aaf4757f5b394cf62866df89))
- Merge origin/main and resolve issues.jsonl conflict([089c7ea](https://github.com/sussdorff/claude-code-plugins/commit/089c7eab6b7829346f705aa0f1c519efa97ef14d))
- Merge latest origin/main (resolve memory ordering in issues.jsonl)([8ed63e0](https://github.com/sussdorff/claude-code-plugins/commit/8ed63e01cddc364f85efce26923857b06b76ee45))

### Refactoring

- **CCP-zrp**: Extract inline code blocks to scripts in 4 beads-workflow skills([3237f6d](https://github.com/sussdorff/claude-code-plugins/commit/3237f6d61d1f60abda8a4fdb6e23cbc90c76ace7))
- **CCP-bjy**: Extract billing-reviewer inline bash block to scripts/launch-billing-review.sh([da9aee9](https://github.com/sussdorff/claude-code-plugins/commit/da9aee970df46e1de6552c8c2128ca8d65b6ab8c))
- **CCP-nvs**: Extract inline shell blocks to scripts in cmux-browser and cmux-markdown([b228d65](https://github.com/sussdorff/claude-code-plugins/commit/b228d6581c158fdc48de0e8dd5cdb7329ac9c5e6))
- **CCP-d0q**: Extract inline code blocks to scripts in hook-creator and vision-review([c1c0436](https://github.com/sussdorff/claude-code-plugins/commit/c1c043642747609a203f9718d199e107daa4c9aa))

### Merge

- Worktree-bead-CCP-0ho([a2ec144](https://github.com/sussdorff/claude-code-plugins/commit/a2ec144fa71f78f6b412be8407bb1c294bb90479))
- Worktree-bead-CCP-bjy([3708645](https://github.com/sussdorff/claude-code-plugins/commit/37086457623c03343b5daef0ffd463b11b4af107))
- Worktree-bead-CCP-d0q([beb4584](https://github.com/sussdorff/claude-code-plugins/commit/beb45841b96c0b225d37f5ddc37b2a1441a4ddbb))
- Worktree-bead-CCP-nvs([d50efe5](https://github.com/sussdorff/claude-code-plugins/commit/d50efe5707ecc2b3d3e6a7da9e97ff810869c0fd))
## [2026.04.102] - 2026-04-23

### Bug Fixes

- **CCP-0ho**: Correct council path check from malte/ to business/ in Phase 3([cd3f92d](https://github.com/sussdorff/claude-code-plugins/commit/cd3f92d9a55a9b08c8ab4a89e5007f04b5c4e5c9))
- **CCP-0ho**: Correct council-roles.yml default path from malte/ to business/([4db6123](https://github.com/sussdorff/claude-code-plugins/commit/4db6123b88c075a91ac10240dc893ce53a4c0eb2))
- **CCP-gzi**: Address review findings iteration 1([a13bc02](https://github.com/sussdorff/claude-code-plugins/commit/a13bc02108c3a9d62988612557491730137406b3))
- **CCP-gzi**: Add CommandRunner DI seams + tests for wave-dispatch/wave-status([32070d6](https://github.com/sussdorff/claude-code-plugins/commit/32070d6c009186c0ab260066cdf78a134cdb8c71))

### Features

- **CCP-gzi**: Green — metrics-start.py + metrics-rollup.py Python ports([98aef15](https://github.com/sussdorff/claude-code-plugins/commit/98aef15cf3d15144bd0ded7644b802a8edb6b22f))
- **CCP-gzi**: Green — codex-exec.py + all wave scripts Python ports([59c1128](https://github.com/sussdorff/claude-code-plugins/commit/59c11283b0e13ba5917cc8e67d61ac47c5d662f2))
- **CCP-gzi**: Green — remove .sh scripts, update all callers to .py([09e2132](https://github.com/sussdorff/claude-code-plugins/commit/09e213230932020a8a38383ee79d1ff768a1e8a8))

### Miscellaneous

- Resolve merge conflicts from origin/main (CHANGELOG + issues.jsonl)([b01fb3e](https://github.com/sussdorff/claude-code-plugins/commit/b01fb3e84b5a2b007071f396e7bebb11c60aa82c))
- **CCP-ahs**: Sync issues.jsonl after merge resolution([b0351e0](https://github.com/sussdorff/claude-code-plugins/commit/b0351e0fd0c2421c93550fcf4532f59d766fcedb))
- **CCP-0ho**: Sync issues.jsonl state([6e45bc4](https://github.com/sussdorff/claude-code-plugins/commit/6e45bc4184271888e26303de52412531f81b63ce))
- **CCP-gzi**: Sync issues.jsonl state pre-ship([8e184ea](https://github.com/sussdorff/claude-code-plugins/commit/8e184ea1e921674a547aedbda1b5eadbb2ce8c01))
- **CCP-gzi**: Sync issues.jsonl after second merge from main([8d740b5](https://github.com/sussdorff/claude-code-plugins/commit/8d740b587d867971cd294b446a6248ca9526fbef))
## [2026.04.101] - 2026-04-23

### Bug Fixes

- **CCP-ahs**: Address review findings iteration 1([fff4e50](https://github.com/sussdorff/claude-code-plugins/commit/fff4e502b9aa22209381fdc38d7491c5dfafa077))
- **CCP-ahs**: Address codex adversarial findings([1af59c2](https://github.com/sussdorff/claude-code-plugins/commit/1af59c21e34adc22eb6b893595c339475310815c))
- **CCP-xib**: Remove screen-lock check; treat push failure as non-blocker([5193565](https://github.com/sussdorff/claude-code-plugins/commit/51935655122f63c6a53521a1ec0328e1c49de7e6))
- **CCP-xib**: Remove remaining screen_locked references from docs([a5e8a36](https://github.com/sussdorff/claude-code-plugins/commit/a5e8a36966c989503183aff1e88c61cdeeeec653))
- **CCP-xib**: Surface push error detail and retry hint in summary; add settings.json trailing newline([f5c5157](https://github.com/sussdorff/claude-code-plugins/commit/f5c5157920262ed5534bec935207e7570af5e6aa))
- **CCP-xib**: Address codex adversarial findings([233dfd4](https://github.com/sussdorff/claude-code-plugins/commit/233dfd44ce9433b9f4814ba739e9cf951e7b1553))
- **CCP-xib**: Remove stale screen-lock reference from phase-b-ship.sh header comment([575c0cc](https://github.com/sussdorff/claude-code-plugins/commit/575c0ccbdca70951ee9b3df438dd04423bc90a11))

### Documentation

- Make harness authoring rules discoverable across sessions([8cd8115](https://github.com/sussdorff/claude-code-plugins/commit/8cd811525511bb4459ab6d8daef125e859f38d0e))

### Features

- **CCP-ahs**: Green — AK1/AK6/AK7 claim.py module with CommandRunner DI([af5e505](https://github.com/sussdorff/claude-code-plugins/commit/af5e5057d9f9a74a6a2bcf96fa16d0c22a7d86cd))
- **CCP-ahs**: Green — AK2 claim-bead.py CLI wrapper with all 4 flags([422b93f](https://github.com/sussdorff/claude-code-plugins/commit/422b93f3289a86376b5fd1b633b9ff8e773553d4))
- **CCP-ahs**: Green — AK4 wave-dispatch.sh pre-dispatch filter([d823489](https://github.com/sussdorff/claude-code-plugins/commit/d823489d4a071aff17593ba1159c87e4a7d21b71))
- **CCP-ahs**: Green — AK5 update agent markdown claim sections to use claim-bead.py([80e6c2d](https://github.com/sussdorff/claude-code-plugins/commit/80e6c2dd382814cbd8a81b5a2352e9720e44200d))

### Miscellaneous

- **CCP-ahs**: Add changelog entry([992e807](https://github.com/sussdorff/claude-code-plugins/commit/992e8072d063c4379c5a0db1de17f7c2c64bd831))
- **CCP-xib**: Update changelog([b67d19f](https://github.com/sussdorff/claude-code-plugins/commit/b67d19facc20cff52a3192c5e50b0e753c02eb14))
- **CCP-xib**: Final issues.jsonl sync before ship([ec6a6eb](https://github.com/sussdorff/claude-code-plugins/commit/ec6a6eb49270ea1e3598f977fa240c7f2de99cfa))

### Testing

- **CCP-ahs**: Red — claim module test suite with all 5 AK7 scenarios([bd8c22b](https://github.com/sussdorff/claude-code-plugins/commit/bd8c22b8b2dabd5746d37df457ead36127468b5f))

### Merge

- Worktree-bead-CCP-xib([823cc4d](https://github.com/sussdorff/claude-code-plugins/commit/823cc4db9cad29b43ac78448f742bc666ec7aaa4))
## [2026.04.100] - 2026-04-22

### Bug Fixes

- **CCP-67x**: Address review findings — version-control TOMLs, Phase 3, WAVE_ID, evidence doc([2aa7859](https://github.com/sussdorff/claude-code-plugins/commit/2aa7859bf5de4e91b94663e1153e4f83cd9cd0ad))

### Features

- **CCP-67x**: Codex bead-orchestrator and wave-orchestrator TOML agents + evidence([c8368d2](https://github.com/sussdorff/claude-code-plugins/commit/c8368d25348ee4131c00656b3576b7700f8049c3))

### Miscellaneous

- Preserve unreleased changelog entry before merge([fd9371f](https://github.com/sussdorff/claude-code-plugins/commit/fd9371f636767d659bbdeb98ccfdaf192ff67039))
- **CCP-67x**: Update changelog([df182d7](https://github.com/sussdorff/claude-code-plugins/commit/df182d72318d1bbe1a6238762d4d8d75be0f9abb))
- **CCP-67x**: Stage bead state updates to issues.jsonl([165ad4e](https://github.com/sussdorff/claude-code-plugins/commit/165ad4e59b7100f6657691bfa3e66c8421370033))
- **CCP-67x**: Sync issues.jsonl after main merge([49afc79](https://github.com/sussdorff/claude-code-plugins/commit/49afc79062f5d4e03c6e48290111c9e300f1802b))
- **CCP-67x**: Re-export issues.jsonl (memory order normalisation)([dc7eb1f](https://github.com/sussdorff/claude-code-plugins/commit/dc7eb1f9ef40926765bfd3eb1f73607af0662c67))
- **CCP-67x**: Final issues.jsonl sync before ship([dce9839](https://github.com/sussdorff/claude-code-plugins/commit/dce9839afb40143c79f2d1f2df1059610e3de954))
## [2026.04.99] - 2026-04-22

### Bug Fixes

- HANDLERS_DIR path bug + ci-monitor + git-state helpers for session-close([14c0e01](https://github.com/sussdorff/claude-code-plugins/commit/14c0e0100f0375a1c2e5214a9659d152eede7cb3))
## [2026.04.98] - 2026-04-22

### Bug Fixes

- **CCP-1bo**: Wave-dispatch --surface flag, scenario pre-flight gate([5ea1719](https://github.com/sussdorff/claude-code-plugins/commit/5ea1719d9edcdf972995a5d731665839b60af178))

### Miscellaneous

- Add embeddeddolt/ to .gitignore + skill-audit CI workflow([bad7135](https://github.com/sussdorff/claude-code-plugins/commit/bad7135f51a0b7e0f3dadabfa7e33fe3fffd9383))
- **CCP-1bo**: Bump version to 2026.04.98 and release changelog([ac06e4b](https://github.com/sussdorff/claude-code-plugins/commit/ac06e4b27dd3f223ed44b1cd5beb44755de4d728))
## [2026.04.97] - 2026-04-22

### Miscellaneous

- **CCP-o4z**: Bump version to 2026.04.97 and release changelog([e994695](https://github.com/sussdorff/claude-code-plugins/commit/e994695503762c3f8d69a72bc155b5d778f3f42e))
## [2026.04.96] - 2026-04-22

### Features

- Session-close serializer + wave-orchestrator single-instance guard([1414e05](https://github.com/sussdorff/claude-code-plugins/commit/1414e057882d82f426a6d380cf9284b89dfa629b))
- Skill-auditor validator, wave-dispatch workspace fix, planning docs([8c6e205](https://github.com/sussdorff/claude-code-plugins/commit/8c6e20572c5c7f4840f77a58e5cde7add33c6c5d))

### Miscellaneous

- **CCP-28l**: Update bead state for session close([4d397c1](https://github.com/sussdorff/claude-code-plugins/commit/4d397c1394d20883551d762f5b374579bce983a6))
## [2026.04.95] - 2026-04-22

### Miscellaneous

- Merge origin/main into worktree-bead-CCP-28l (resolve issues.jsonl conflict)([f4bffb1](https://github.com/sussdorff/claude-code-plugins/commit/f4bffb170b33726a6425fb56cf3aed2110254fff))
- **CCP-28l**: Bump version to 2026.04.95 and release changelog([54821f9](https://github.com/sussdorff/claude-code-plugins/commit/54821f95f25b2531d1e8c4f6926d10865adb0c2d))
## [2026.04.94] - 2026-04-22

### Bug Fixes

- **wave-monitor**: Reduce poll interval from 270s to 60s([63bf648](https://github.com/sussdorff/claude-code-plugins/commit/63bf6487b307ef0e566c9c7f9c68d75679d344ab))
- **CCP-o4z**: Address review findings iteration 1([f9de704](https://github.com/sussdorff/claude-code-plugins/commit/f9de7045ea72adc439956273f274ed574d2ce690))
- **CCP-o4z**: Address codex adversarial findings([a1f7fcb](https://github.com/sussdorff/claude-code-plugins/commit/a1f7fcb6a918bbcd467e2437ef81ffb6c90730a2))
- **CCP-28l**: Fix prompt tail-truncation and document timeout Bash wrapper alignment([8e44b33](https://github.com/sussdorff/claude-code-plugins/commit/8e44b3332694b0f8b654ed89f121369d503c7625))
- **CCP-6s1**: Match exclude-pattern against relative path not absolute([bdce9da](https://github.com/sussdorff/claude-code-plugins/commit/bdce9dac86067c4bb53aab255ee80d1907e58b29))

### Documentation

- **CCP-28l**: Document Codex timeout threshold and add pre-truncation guard([8c05e75](https://github.com/sussdorff/claude-code-plugins/commit/8c05e75333a59a0320d7f3b3e5b73d76fb7088aa))

### Features

- **CCP-o4z**: Green — session-end Stop hook for beads-workflow([fef7a27](https://github.com/sussdorff/claude-code-plugins/commit/fef7a279fea83d86620c790051e7577ba04558ab))
- **CCP-6s1**: Add --exclude-pattern flag to check-debrief-adherence.py([c4384e9](https://github.com/sussdorff/claude-code-plugins/commit/c4384e9fc91f9b7150fbc4127b2ee6c8dba0b781))

### Miscellaneous

- **CCP-6s1**: Update bead state for session close([37681a7](https://github.com/sussdorff/claude-code-plugins/commit/37681a704ceac4cceb99dbf7a054385c1e76e849))
- **CCP-6s1**: Bump version to 2026.04.94 and release changelog([24c149b](https://github.com/sussdorff/claude-code-plugins/commit/24c149ba540be0f8ca14b4ce2b2a80e0988d29d4))

### Testing

- **CCP-o4z**: Red — session-end hook test suite([221ebad](https://github.com/sussdorff/claude-code-plugins/commit/221ebaddbee5311999d3143f51ebe07d00905355))
## [2026.04.93] - 2026-04-22

### Bug Fixes

- **CCP-4gi**: Sync TOML port with session-close.md handoff and metadata.source changes([211adbb](https://github.com/sussdorff/claude-code-plugins/commit/211adbbf082d93a17f4b923cfaf98c713ed17bb6))

### Miscellaneous

- **CCP-4gi**: Bump version to 2026.04.93 and release changelog([d350acc](https://github.com/sussdorff/claude-code-plugins/commit/d350acc09f7eb14d5f97593fd83b711d3c4a7c06))

### Refactoring

- **CCP-4gi**: Enrich session-close debrief with handoff aggregation and metadata.source([d7e1182](https://github.com/sussdorff/claude-code-plugins/commit/d7e1182ee36dacc1aa3f41e8cf95c8e88d351d9e))
## [2026.04.92] - 2026-04-22

### Miscellaneous

- **CCP-5xe**: Bump version to 2026.04.92 and release changelog([7cdc85d](https://github.com/sussdorff/claude-code-plugins/commit/7cdc85d2b83c132879c61ecbc79707888bd04c77))
## [2026.04.91] - 2026-04-22

### Bug Fixes

- **codex-exec**: Redirect stdin from /dev/null to prevent interactive wait([48c458b](https://github.com/sussdorff/claude-code-plugins/commit/48c458be5a7d875d60fd48e6b1fca90503f73534))
## [2026.04.90] - 2026-04-22

### Bug Fixes

- **CCP-e7a**: Remove debrief from strict-output agents, exempt in standard, fix scout fence([52af7f3](https://github.com/sussdorff/claude-code-plugins/commit/52af7f363a96feb6ba71c2ce8011ba22b7d9447e))

### Features

- **codex-exec**: Add --diff-range flag for inline vs self-collect diff handling([6cdd589](https://github.com/sussdorff/claude-code-plugins/commit/6cdd5890815fcd095e699fa01c38bb6d54d67d13))
## [2026.04.89] - 2026-04-22

### Miscellaneous

- **CCP-e7a**: Bump version to 2026.04.89 and release changelog([66a2738](https://github.com/sussdorff/claude-code-plugins/commit/66a27380168bc99ec1ec55e9bb4f5fec5ced10ae))
## [2026.04.88] - 2026-04-22

### Bug Fixes

- **CCP-5xe**: Fix shell-unsafe debrief piping and handoff file cleanup([3b305d2](https://github.com/sussdorff/claude-code-plugins/commit/3b305d28eaa2445e5ac2b7effb71ff88b3d5ec5a))
- **CCP-5xe**: Safe JSON serialization via tempfile, preserve handoff for debrief-only retries([0cc757b](https://github.com/sussdorff/claude-code-plugins/commit/0cc757bb55b04427eefc0db1331c42f8a8f592d6))

### Features

- **CCP-e7a**: Add debrief template to all non-exempt agent prompts([ce00d1e](https://github.com/sussdorff/claude-code-plugins/commit/ce00d1eb02b2fca6cb2344b602b085f6c078fc29))

### Miscellaneous

- **CCP-5xe**: Bump version to 2026.04.88 and release changelog([5392336](https://github.com/sussdorff/claude-code-plugins/commit/5392336b82104fe4be88ab245a44f528ec13e0ea))

### Refactoring

- **CCP-5xe**: Bead-orchestrator aggregates subagent debriefs via parse_debrief.py and handoff file([6eefd27](https://github.com/sussdorff/claude-code-plugins/commit/6eefd27c2099530461e9f15554f0402dafc422cb))
## [2026.04.87] - 2026-04-22

### Miscellaneous

- **CCP-9bm**: Merge main into feature branch, resolve changelog conflict([92032c4](https://github.com/sussdorff/claude-code-plugins/commit/92032c4424f68e4c438b58deef16243467656c9c))
- **CCP-9bm**: Bump version to 2026.04.87 and release changelog([6117f2d](https://github.com/sussdorff/claude-code-plugins/commit/6117f2dab7b17cdc67218f27e47ad7e6fc044b51))
## [2026.04.86] - 2026-04-22

### Bug Fixes

- **CCP-k1m**: Address review findings iteration 1([bbac684](https://github.com/sussdorff/claude-code-plugins/commit/bbac684b9a55a9d88dad0ac01ff79452e446efd9))

### Documentation

- **CCP-9bm**: Add changelog entry for debrief return contract([a20546c](https://github.com/sussdorff/claude-code-plugins/commit/a20546c58b9e0da77ab8a211e6ee16f7ce5b3699))

### Features

- **CCP-9bm**: Green — parse_debrief.py stdlib parser for subagent debrief sections([e0450c1](https://github.com/sussdorff/claude-code-plugins/commit/e0450c1666a7ff044fff9d7a5a8e7f2a1f9a24e7))
- **CCP-9bm**: Green — check-debrief-adherence.py lint script + test import fix([6354fda](https://github.com/sussdorff/claude-code-plugins/commit/6354fdae2db9a1a89296e368bff82004f49b6f23))
- **CCP-9bm**: Green — add debrief template to 5 required agent prompts([963ebdc](https://github.com/sussdorff/claude-code-plugins/commit/963ebdc9175b33198c50e8338b17552b1fa16000))
- **CCP-k1m**: Non-interactive session-close mode with resume support([d23f667](https://github.com/sussdorff/claude-code-plugins/commit/d23f6674fc94c2043cf7a5d59e405d24cd1d15c1))

### Miscellaneous

- **CCP-k1m**: Bump version to 2026.04.86 and release changelog([c7c414f](https://github.com/sussdorff/claude-code-plugins/commit/c7c414f49d30e11fbe0ff1766b5ea7a08b4f5ebc))

### Testing

- **CCP-9bm**: Red — parse_debrief test suite (all 4 headings, embedded, empty sections, CLI)([b45b3cd](https://github.com/sussdorff/claude-code-plugins/commit/b45b3cdf837923decc8052bdd43b7bdb7f3528d5))
- **CCP-9bm**: Red — check-debrief-adherence test suite (conforming, missing, exempt, CLI)([f682acb](https://github.com/sussdorff/claude-code-plugins/commit/f682acb20c26c2216193cfa9f5e0309ac8799fec))
- **CCP-k1m**: Red — non-interactive session-close mode test suite([a831671](https://github.com/sussdorff/claude-code-plugins/commit/a831671bb69b0cd846d46e2ddee882a368dc2dba))
## [2026.04.85] - 2026-04-22

### Bug Fixes

- **CCP-6up.5**: Address review findings iteration 1([6f76082](https://github.com/sussdorff/claude-code-plugins/commit/6f76082ada34bbaf8f2e2d088273c8e096f7df29))
- **CCP-6up.5**: Address auto-fixable verification disputes([97d8404](https://github.com/sussdorff/claude-code-plugins/commit/97d8404460343c1e4505a2121e794ca6e192c8de))
- **CCP-6up.5**: Correct bead-metrics inventory row and remove obsolete __future__ import([6d7e0ac](https://github.com/sussdorff/claude-code-plugins/commit/6d7e0ac730f580bd056d660d8ff31ee3be2dde5d))

### Miscellaneous

- **CCP-6up.5**: Update bead state for session close([ad4a668](https://github.com/sussdorff/claude-code-plugins/commit/ad4a668eb3907e7f76649cd990d400e71f6d4674))

### Refactoring

- **CCP-6up.5**: Green — add increment_auto_decisions to metrics.py([43d4946](https://github.com/sussdorff/claude-code-plugins/commit/43d4946b9a91dd4717e2400883781bdf4c1747d5))
- **CCP-6up.5**: Green — extract wave-monitor bash to wave-poll.py([632ca83](https://github.com/sussdorff/claude-code-plugins/commit/632ca83ac97ecd45a1598179f357142ff0890598))
- **CCP-6up.5**: Green — update agents and smoke test to use extracted helpers([c24c690](https://github.com/sussdorff/claude-code-plugins/commit/c24c69057e04d904392fdfec3b6277776d58e485))

### Testing

- **CCP-6up.5**: Red — increment_auto_decisions tests([2f7e6b1](https://github.com/sussdorff/claude-code-plugins/commit/2f7e6b1d95a36e92e15c582beb6feef6668fdb66))
- **CCP-6up.5**: Red — wave-poll.py unit tests([c05b276](https://github.com/sussdorff/claude-code-plugins/commit/c05b27610b2a8065d75f81653b1ea9f358679fe1))
## [2026.04.82] - 2026-04-22

### Bug Fixes

- **CCP-hf1**: Address review findings iteration 1([eed20c9](https://github.com/sussdorff/claude-code-plugins/commit/eed20c9d8aaae9e69d8c9dd6becab29796ee0d62))
- **CCP-6up.3**: Address review findings iteration 1([76e8379](https://github.com/sussdorff/claude-code-plugins/commit/76e83793369cfba020cd16ac91d176648fffc3b8))
- **wave-dispatch**: Propagate WAVE_ID into bead_runs.wave_id([9fb07de](https://github.com/sussdorff/claude-code-plugins/commit/9fb07de966d9bb172422cf25a1c736350f926716))
- **wave-completion**: Fix metrics sanity check defaults and safety([1f64a92](https://github.com/sussdorff/claude-code-plugins/commit/1f64a92fe66dd427c55982f7c190d1b06024df32))
- **CCP-a67**: Address review findings iteration 1([2c5706b](https://github.com/sussdorff/claude-code-plugins/commit/2c5706bef974e48b36bf7a41a40f2e9276f566ab))

### Documentation

- **CCP-hf1**: Update changelog with vision-author skill([2a6e8fa](https://github.com/sussdorff/claude-code-plugins/commit/2a6e8faaab2f1753bb28c256d77398344c72bc48))
- Update changelog for CCP-6up.3 (skill-authoring Enforcer-Reactive)([f854e04](https://github.com/sussdorff/claude-code-plugins/commit/f854e04ee8b035b67e77bbd3fafc09b777f8241d))

### Features

- **CCP-hf1**: Green — vision_renderer.py and vision_conformance.py([60a6d6a](https://github.com/sussdorff/claude-code-plugins/commit/60a6d6af63ca24b618386918153008dd69048489))
- **CCP-hf1**: Green — vision-author skill, template, smoke-test checklist([269ff26](https://github.com/sussdorff/claude-code-plugins/commit/269ff26d53b9e3b8aad3a7b2d164115861e02fca))
- **CCP-6up.3**: Green — add validate-skill.py for EXTRACTABLE_CODE enforcement in SKILL.md([9ae1564](https://github.com/sussdorff/claude-code-plugins/commit/9ae1564c3787b327bc74e46238de4ab356226728))
- **CCP-6up.3**: Green — wire validate-skill into skill-auditor SKILL.md and agent([f5ab9a0](https://github.com/sussdorff/claude-code-plugins/commit/f5ab9a06f99381499e8382efcf153f0609b7237c))
- **CCP-a67**: Green — vision_review.py + mock_council fixture (22 tests passing)([a055220](https://github.com/sussdorff/claude-code-plugins/commit/a0552203d4ae081349ba8f7ecf3bc5aeccafb405))
- **CCP-a67**: Add vision-review SKILL.md with trinity_role enforcer-reactive([6067964](https://github.com/sussdorff/claude-code-plugins/commit/60679645b9c053e08bf91f5870d667762e1500d0))

### Miscellaneous

- **open-brain-7lz**: Bump version to 2026.04.81, update changelog([a66873a](https://github.com/sussdorff/claude-code-plugins/commit/a66873a12ec0bbc588993e4b54b9e0fb55014ed1))
- **CCP-a67**: Update bead state and changelog([665180b](https://github.com/sussdorff/claude-code-plugins/commit/665180b007d7cd15938d0d2dc172bdd0b653ccad))
- **CCP-a67**: Add changelog entry for vision-review skill([038400d](https://github.com/sussdorff/claude-code-plugins/commit/038400dc112e180b49a19162062f0e123ba77bd8))
- **CCP-a67**: Update bead state for session close([317c0a3](https://github.com/sussdorff/claude-code-plugins/commit/317c0a3b5ea4d186777330ad467b1f9093f14eb8))

### Testing

- **CCP-hf1**: Red — vision-author unit tests (renderer, conformance, tense-gate)([1ec64b8](https://github.com/sussdorff/claude-code-plugins/commit/1ec64b8dbfeecd5995dedec4713496859fd19f34))
- **CCP-6up.3**: Red — EXTRACTABLE_CODE enforcement tests for validate-skill.py([62e4b10](https://github.com/sussdorff/claude-code-plugins/commit/62e4b10863c01bf454ba6831362762dcb48f9b1f))
- **CCP-a67**: Red — vision-review test suite (health score, ADR gen, report gen, smoke)([98f5384](https://github.com/sussdorff/claude-code-plugins/commit/98f5384cebe91aeedf1135940ba78f1dcdaaa755))
## [2026.04.80] - 2026-04-22

### Bug Fixes

- **codex-exec**: Degrade gracefully when metrics DB unavailable([7381518](https://github.com/sussdorff/claude-code-plugins/commit/7381518521910a4652231955073e1b62e70b3b1b))

### Features

- Add script-first execution result contract([094b3ed](https://github.com/sussdorff/claude-code-plugins/commit/094b3ed161b39f062329bf9bb500e135c97f6c6f))

### Miscellaneous

- Update changelog([7882114](https://github.com/sussdorff/claude-code-plugins/commit/78821147324d4805284099063d225bea93715f78))

### Refactoring

- **beads-workflow**: Extract inline metrics code into dedicated shell scripts([be1f8a5](https://github.com/sussdorff/claude-code-plugins/commit/be1f8a5ec65bb1fc0ec322eb323b60461b460e88))
## [2026.04.79] - 2026-04-22

### Bug Fixes

- **CCP-9yd**: Address review findings iteration 1([07a1814](https://github.com/sussdorff/claude-code-plugins/commit/07a1814e950d291f30bd6204669e065f3070d255))

### Features

- **CCP-9yd**: Add Codex session-close agent TOML with gap documentation([b451d24](https://github.com/sussdorff/claude-code-plugins/commit/b451d242fa29a020646f6020eb81fd5cec5fb103))

### Miscellaneous

- Sync issues.jsonl from main merge([5bdc161](https://github.com/sussdorff/claude-code-plugins/commit/5bdc16197ae28b8de45800ea242b545a04a558de))
- Merge worktree-bead-CCP-9yd (resolve evidence file conflict)([4a3f052](https://github.com/sussdorff/claude-code-plugins/commit/4a3f052325e8eacd8baaad05583bceb0a5d0cfd9))
## [2026.04.78] - 2026-04-22

### Bug Fixes

- **CCP-e2r**: Address review findings — idempotency, error handling, regex fixes([1fdad81](https://github.com/sussdorff/claude-code-plugins/commit/1fdad81c82b7057fdbb8c7c5131220f2fe26d1f6))
- **CCP-9yd**: Address review findings iteration 1([515b02b](https://github.com/sussdorff/claude-code-plugins/commit/515b02befc6efe2ec3a482cca8542f38a479093f))

### Features

- **CCP-9yd**: Green — create Codex session-close agent TOML([4de2679](https://github.com/sussdorff/claude-code-plugins/commit/4de2679516505bef7b7232eb7d66f4cef5ec9d60))
- **CCP-e2r**: Collapse session-close step-handlers into phase-level batch handlers([87a5f43](https://github.com/sussdorff/claude-code-plugins/commit/87a5f43b74ec5e019028a822505c06fcfca939bf))
- **CCP-9yd**: Add E2E evidence for Codex session-close agent run([8bb063f](https://github.com/sussdorff/claude-code-plugins/commit/8bb063fad487138845b323472edd5610a60a2eb2))

### Miscellaneous

- Update changelog for CCP-e2r([15cda1c](https://github.com/sussdorff/claude-code-plugins/commit/15cda1c9955c1245d3cdcebd3974a3d56af120ec))

### Testing

- **CCP-9yd**: Red — validate codex session-close agent TOML structure([5bc3bab](https://github.com/sussdorff/claude-code-plugins/commit/5bc3bab68732cd545d8d16e873bac00ab01bc83c))
## [2026.04.77] - 2026-04-22

### Miscellaneous

- **CCP-8tb**: Sync trampoline stub to .agents/skills/skill-auditor([3aac497](https://github.com/sussdorff/claude-code-plugins/commit/3aac497f2280724072bdf8a62ab6c25221c65c65))
## [2026.04.76] - 2026-04-22

### Features

- **CCP-dnk**: Port wave-orchestrator to Sonnet subagent, wire in wave-monitor([560ed0a](https://github.com/sussdorff/claude-code-plugins/commit/560ed0af4d02cf1c9e50f77117e5cf7a9fb475a7))

### Miscellaneous

- **CCP-dnk**: Update changelog for wave-orchestrator agent migration([1df933f](https://github.com/sussdorff/claude-code-plugins/commit/1df933fbe48ef5890b0d5abf8c034368418177a0))
## [2026.04.75] - 2026-04-22

### Bug Fixes

- **CCP-793**: Harden quick-fix session-close handoff([715996a](https://github.com/sussdorff/claude-code-plugins/commit/715996ab9fc4e623745ba00bc4a6aa059ae077f4))
- **skill-auditor**: Flag description overflow >1024 chars as blocking([5062f9f](https://github.com/sussdorff/claude-code-plugins/commit/5062f9f0ebe67329200546478d66e5d1e49de690))

### Features

- **session-close**: Auto-deploy codex skills after CC plugin update([2f3d0ae](https://github.com/sussdorff/claude-code-plugins/commit/2f3d0aede8197f9f4b5f519de269342b05067b27))

### Miscellaneous

- Update changelog([b3e5993](https://github.com/sussdorff/claude-code-plugins/commit/b3e599345d969fdd5105297acdbebcf88e1cb1a7))
## [2026.04.74] - 2026-04-22

### Features

- **CCP-aoc**: Add wave-monitor Haiku agent for wave polling([5144456](https://github.com/sussdorff/claude-code-plugins/commit/5144456560f1b3c911c54f3317a3b958b245bafb))

### Miscellaneous

- **CCP-aoc**: Update changelog for wave-monitor agent([7e205c0](https://github.com/sussdorff/claude-code-plugins/commit/7e205c02c9d521257e9c61f2daf5016d836d0bc8))

### Testing

- **CCP-aoc**: Add smoke test for wave-monitor verdict routing([90e6528](https://github.com/sussdorff/claude-code-plugins/commit/90e652806357473c4463f61abd0c8fca3e721570))
## [2026.04.73] - 2026-04-21

### Features

- **CCP-8tb**: Convert skill-auditor to Opus subagent with trampoline skill([7d1f732](https://github.com/sussdorff/claude-code-plugins/commit/7d1f732d59e090f7c1904ca48aff510ee25f8805))

### Miscellaneous

- **CCP-8tb**: Update changelog for skill-auditor subagent migration([464bc04](https://github.com/sussdorff/claude-code-plugins/commit/464bc044fa0972a17b054bb0c2296acd44bd6995))

### Research

- **CCP-ar0**: Document parent-session parking spike verdict([de01b61](https://github.com/sussdorff/claude-code-plugins/commit/de01b611fcbdf03bd1c524e3bb06497bcd6a63c0))
## [2026.04.72] - 2026-04-21

### Bug Fixes

- **CCP-9xy**: Harden bead agents against mid-flow stops and session-close handoff failures([fe9f047](https://github.com/sussdorff/claude-code-plugins/commit/fe9f0475cdc6fd0691964fa39ad6903917b54162))
- **CCP-1m6**: Address codex adversarial findings — non-hermetic test, namespace filter, orchestrator_handled([d2c639a](https://github.com/sussdorff/claude-code-plugins/commit/d2c639ac5dad9d9b6398f2109ea7e044f123bafa))

### Miscellaneous

- **CCP-1m6**: Update changelog([b05a3f3](https://github.com/sussdorff/claude-code-plugins/commit/b05a3f31cf01ba256d99b8b4e6302ed0edf9b111))

### Testing

- **CCP-1m6**: Add structural coverage test for agent-standards.yml([e91570a](https://github.com/sussdorff/claude-code-plugins/commit/e91570a440af9af0c47bce21cbba49dab3ab8c2c))

### Merge

- Worktree-bead-CCP-1m6([643be96](https://github.com/sussdorff/claude-code-plugins/commit/643be96fdf3843edbcb72b2b0a1a20e1e64e869a))
## [2026.04.71] - 2026-04-21

### Miscellaneous

- **CCP-imb**: Sync issues.jsonl post-merge([c79758b](https://github.com/sussdorff/claude-code-plugins/commit/c79758b3770e6cbf42b8e7be044c37afd21905d3))
- **CCP-imb**: Absorb issues.jsonl auto-export drift([3989f21](https://github.com/sussdorff/claude-code-plugins/commit/3989f210d91d86db702a05b2d04860dc92eb735f))
- **CCP-imb**: Stabilize issues.jsonl export([12a4c81](https://github.com/sussdorff/claude-code-plugins/commit/12a4c81787c3e1f5a386b0e8edd1235694755d05))
- **CCP-imb**: Add CHANGELOG entry for rollup_run null-safety([938419b](https://github.com/sussdorff/claude-code-plugins/commit/938419b3ac6a2612569687427fbce6eb6358f242))

### Merge

- Worktree-bead-CCP-imb([509737f](https://github.com/sussdorff/claude-code-plugins/commit/509737fcdaacff796cc24e9910cd9efe1c998ca3))
## [2026.04.70] - 2026-04-21

### Miscellaneous

- **CCP-2hd.1**: Move changelog entry to [unreleased] after folded merge from main([a8a76dc](https://github.com/sussdorff/claude-code-plugins/commit/a8a76dca4bce6258e726aaba5c04af92ba760e7e))

### Merge

- Worktree-bead-CCP-2hd.1([30cda94](https://github.com/sussdorff/claude-code-plugins/commit/30cda9466c3b4a7a9d722aa0fb3fb3e2dc14f039))
## [2026.04.69] - 2026-04-21

### Miscellaneous

- **CCP-dzp**: Sync issues.jsonl after merge([68510e5](https://github.com/sussdorff/claude-code-plugins/commit/68510e5632c37af7d9446668ea6fc8f155c74d07))

### Merge

- Worktree-bead-CCP-dzp([6ca4501](https://github.com/sussdorff/claude-code-plugins/commit/6ca45019a22ef177ff9904951e33b5aa0bbf4739))
## [2026.04.68] - 2026-04-21

### Bug Fixes

- **CCP-dzk**: Address codex adversarial findings([d8dbbb3](https://github.com/sussdorff/claude-code-plugins/commit/d8dbbb3a9ed30325b89b0ad403c7444652990d42))

### Miscellaneous

- **CCP-dzk**: Update changelog([1fa8567](https://github.com/sussdorff/claude-code-plugins/commit/1fa8567754f580b384aa12b7ff6b001a3e90c437))
## [2026.04.67] - 2026-04-21

### Miscellaneous

- Refresh issues.jsonl export([f360915](https://github.com/sussdorff/claude-code-plugins/commit/f36091513edf6250f971463b25b2cb0ed1f533d7))
- Update changelog for CCP-2n7([fb820aa](https://github.com/sussdorff/claude-code-plugins/commit/fb820aa06cfde3ac2af433658c64dc9fb63671af))

### Merge

- Sync issues.jsonl from origin/main([178a2ad](https://github.com/sussdorff/claude-code-plugins/commit/178a2adccd55737733c8541204223895dbd9a44b))
- Worktree-bead-CCP-2n7([39b7709](https://github.com/sussdorff/claude-code-plugins/commit/39b770980575ab48779c683507899c9422e7dd9f))
## [2026.04.66] - 2026-04-21

### Bug Fixes

- **CCP-imb**: Guard rollup_run against null run_id + log orphan agent_calls([748554a](https://github.com/sussdorff/claude-code-plugins/commit/748554adfefae0c64d2c42496001c009510f7b63))
- **CCP-2hd.1**: Address review findings iteration 1([2436c6a](https://github.com/sussdorff/claude-code-plugins/commit/2436c6adf238717961fe9b2f128e533a895cc6b0))
- **CCP-dzp**: Green — propagate codex exec timeout via CODEX_EXEC_TIMEOUT wrapper([0b083d6](https://github.com/sussdorff/claude-code-plugins/commit/0b083d6fa459dafc2e421c5b8b8568d1f03a111d))
- **CCP-2n7**: Address review findings iteration 1([7b339ac](https://github.com/sussdorff/claude-code-plugins/commit/7b339ac99747d9e240179f5008cae0ce3dd3fbc2))
- **CCP-dzk**: Address review findings iteration 1([5c919bb](https://github.com/sussdorff/claude-code-plugins/commit/5c919bb03464977283fd73beed6053efdeb40c26))
- **CCP-mit**: Use subshell cd for bd dolt start in worktree hook([a0c0160](https://github.com/sussdorff/claude-code-plugins/commit/a0c0160de72a53bd235ac56051623cda268ddd9e))
- **CCP-mit**: Handle WorktreeCreate payload format (cwd+name fallback)([60e69ec](https://github.com/sussdorff/claude-code-plugins/commit/60e69ec0b110894c9b86973ee67a187a06e5ee18))
- **CCP-mit**: Exclude worktrees/ from .claude rsync to prevent recursive copies([9243f55](https://github.com/sussdorff/claude-code-plugins/commit/9243f5573a86e699210d26a566ed71f80f732561))

### Features

- **CCP-2hd.1**: Normalize touched_paths to canonical packages before vision boundary check([3d05168](https://github.com/sussdorff/claude-code-plugins/commit/3d05168631fccd0777af73228fb28bc5f62cdd0f))
- **CCP-2n7**: Green — SubagentStop adhoc metrics implementation([64c5221](https://github.com/sussdorff/claude-code-plugins/commit/64c522120366357c4fbcc92dd47aba3aee76e6ed))
- **CCP-dzk**: Green — fix fnmatch normalization and test runner for subagent hook([c49c297](https://github.com/sussdorff/claude-code-plugins/commit/c49c2975f3709c83d3aec2318a97862258ae9138))

### Miscellaneous

- **CCP-imb**: Update beads issues.jsonl with close-reason note([ec3a919](https://github.com/sussdorff/claude-code-plugins/commit/ec3a91928219c0151d15cd8d322bcd1457114afc))
- **CCP-imb**: Sync issues.jsonl pre-merge (bd auto-export)([55463f7](https://github.com/sussdorff/claude-code-plugins/commit/55463f7e8d3f1062d2ee4b4a58437e6504f54ed4))
- **CCP-imb**: Sync issues.jsonl after bd dolt pull([b834219](https://github.com/sussdorff/claude-code-plugins/commit/b834219bc895240b28a167d55e7eb04439c01ba2))
- **CCP-imb**: Final sync issues.jsonl before merge([3a7a4e1](https://github.com/sussdorff/claude-code-plugins/commit/3a7a4e1b82c55d9f40c34ba7360546d7ab30d64d))
- **CCP-2hd.1**: Add changelog entry([244dba0](https://github.com/sussdorff/claude-code-plugins/commit/244dba09c9f3b91cf9fa2ecb25d695c790484bf8))
- **CCP-2hd.1**: Reconcile issues.jsonl before merge from main([2d30fe8](https://github.com/sussdorff/claude-code-plugins/commit/2d30fe8990d91297ea0c8f904619fc48c62c49a4))
- **CCP-dzp**: Refresh issues.jsonl after bd updates([56f5019](https://github.com/sussdorff/claude-code-plugins/commit/56f5019495b1a29a6574266c39a5a38450b57ab9))
- **CCP-mit**: Add WorktreeCreate hook, deprecate worktree-manager([acdcb88](https://github.com/sussdorff/claude-code-plugins/commit/acdcb88665b123d2da73cc907714a97478a116c4))
- **CCP-mit**: Sync issues.jsonl from main merge([0b87c91](https://github.com/sussdorff/claude-code-plugins/commit/0b87c910ec8d9ac4d1d02fef534c788d09cdf9ed))

### Testing

- **CCP-imb**: Red — rollup_run drops silently on null run_id([3033a45](https://github.com/sussdorff/claude-code-plugins/commit/3033a4544583a82b42396a66dd69d2604c172f1b))
- **CCP-dzp**: Red — codex-exec.sh must exit non-zero on timeout([a124b30](https://github.com/sussdorff/claude-code-plugins/commit/a124b3086949f05b184566eab762b965a26731a0))
- **CCP-2n7**: Red — failing tests for SubagentStop adhoc metrics hook([ab16c7e](https://github.com/sussdorff/claude-code-plugins/commit/ab16c7e6eb75505883ead243ae206bd8ab42241d))
- **CCP-dzk**: Red — inject-subagent-standards hook tests([49dbd08](https://github.com/sussdorff/claude-code-plugins/commit/49dbd0870751a9d4bf8051502cdf7fc7cd0927dd))

### Merge

- Worktree-bead-CCP-mit([bbbc9cc](https://github.com/sussdorff/claude-code-plugins/commit/bbbc9cc9467410551ab7adbf6e4194ea4a7a7aa7))
## [2026.04.65] - 2026-04-21

### Merge

- Worktree-bead-CCP-50y([f73a683](https://github.com/sussdorff/claude-code-plugins/commit/f73a6836ff374bb5453d1e77307a59973a841a00))
## [2026.04.64] - 2026-04-21

### Bug Fixes

- **CCP-50y**: Address review findings iteration 1([23c5c82](https://github.com/sussdorff/claude-code-plugins/commit/23c5c822ae161a9fa61f4aeaa2f9d5ee12454704))
- **CCP-rjq**: Address adversarial findings — initialize PHASE_125_ARCH_FINDINGS, dry-run path-B guard, re-review trigger([7fcba08](https://github.com/sussdorff/claude-code-plugins/commit/7fcba0807dabb435d4d8539fcf635cc0bb9e20ad))

### Features

- **CCP-50y**: Green — extend sync-codex-skills with multi-directory registry([73e56eb](https://github.com/sussdorff/claude-code-plugins/commit/73e56ebd3436e834f922fc951e4dc9d315c1b561))
- **CCP-50y**: Green — convert 10 candidate skills to portable format([84956bf](https://github.com/sussdorff/claude-code-plugins/commit/84956bf7a9ab2b7212aeee6dfc6fb4cfd5e77d53))
- **CCP-50y**: Green — sync 10 converted skills to .agents/skills([6ccc5c3](https://github.com/sussdorff/claude-code-plugins/commit/6ccc5c3215dafbaf054e168872da620bf336dd05))
- **CCP-rjq**: Add Phase 1.25 wave-review-gate to wave-orchestrator([c763cb3](https://github.com/sussdorff/claude-code-plugins/commit/c763cb39da05f58f0d96e8e511640b2cffc58c4c))
- **CCP-rjq**: Add Phase 1.25 wave-review-gate to wave-orchestrator([6668314](https://github.com/sussdorff/claude-code-plugins/commit/6668314e63a964586fa94ebb50be741bda8052bf))

### Miscellaneous

- **CCP-50y**: Add changelog entry([49335ff](https://github.com/sussdorff/claude-code-plugins/commit/49335ff218eed2725e7df37ea4889b1f5b153cd8))
- Update changelog (pre-merge commit from main)([9fedeb5](https://github.com/sussdorff/claude-code-plugins/commit/9fedeb5faf42a0a5e25a7ca3362ac7cc931da806))
- **CCP-rjq**: Update bead tracker state([63ee2c2](https://github.com/sussdorff/claude-code-plugins/commit/63ee2c22bfc897522ae5b4d11c781f9e9fa11681))
- **CCP-rjq**: Reconcile issues.jsonl after first merge from main([c43d3a9](https://github.com/sussdorff/claude-code-plugins/commit/c43d3a990074f54b33c7e7ece5baa4892d6f7c91))
- Update changelog([c3022cd](https://github.com/sussdorff/claude-code-plugins/commit/c3022cd494cad9c51c8f9ad1e84ebb4a1354b02e))

### Testing

- **CCP-50y**: Red — portability tests for 10 candidate skills([a27a62f](https://github.com/sussdorff/claude-code-plugins/commit/a27a62fdd5300c3cabd24e916a0a5ee376fbcf33))

### Merge

- Worktree-bead-CCP-rjq([c1e7777](https://github.com/sussdorff/claude-code-plugins/commit/c1e777726e10647c5e69b66f143956288af1d6a1))
## [2026.04.63] - 2026-04-21

### Merge

- Worktree-bead-CCP-pvw([fe6ab34](https://github.com/sussdorff/claude-code-plugins/commit/fe6ab3480947e3cf9e4b1bb0758dbd39b485f35b))
## [2026.04.62] - 2026-04-21

### Bug Fixes

- **CCP-pvw**: Correct quality-B trigger, B/C ambiguity, and output ordering([aacb2b7](https://github.com/sussdorff/claude-code-plugins/commit/aacb2b79fb63c53e128b2eb199d657e83afae559))

### Features

- **CCP-5d0**: Load CLAUDE.md and AGENTS.md when both exist in project-context skill([bc17330](https://github.com/sussdorff/claude-code-plugins/commit/bc17330a6880fc740bd3379df0736fdc09b4695e))

### Merge

- Worktree-bead-CCP-5d0([caf7166](https://github.com/sussdorff/claude-code-plugins/commit/caf716604bc4231a3a898602019507391df39b67))

### Task

- **CCP-pvw**: Absorb factory-check quality criteria into wave-reviewer([f7ce382](https://github.com/sussdorff/claude-code-plugins/commit/f7ce38206b6dcfd9d0da6b15ddbdd6312e1d7437))
## [2026.04.61] - 2026-04-21

### Bug Fixes

- **CCP-2vo.10**: Update model-strategy.yml comment after cmux-reviewer removal([df9071e](https://github.com/sussdorff/claude-code-plugins/commit/df9071ed302e99c886f502f0a2348dfd0b07c306))

### Miscellaneous

- **CCP-2vo.10**: Delete 2-pane review infrastructure([e2342e9](https://github.com/sussdorff/claude-code-plugins/commit/e2342e9690bdbcffde109b8dc3d1e5283369d81a))

### Merge

- **CCP-2vo.10**: Delete 2-pane review infrastructure (cmux-reviewer + cld -br + codex-watch.sh)([7ccd714](https://github.com/sussdorff/claude-code-plugins/commit/7ccd714a690bf3de29f421112be9f43702069316))
## [2026.04.60] - 2026-04-20

### Bug Fixes

- **CCP-2vo.8**: Restore issues.jsonl drift, fix non-existent bd metrics commands([5e9a05a](https://github.com/sussdorff/claude-code-plugins/commit/5e9a05a0c067a5f04544d49ef2644f10a93e906c))
- **CCP-2vo.8**: Replace non-existent wall_clock_s with impl_duration_ms in dispatch query([fc49597](https://github.com/sussdorff/claude-code-plugins/commit/fc4959792e6700d587283122c33ecbd6404873dd))

### Miscellaneous

- Update changelog([3ad1849](https://github.com/sussdorff/claude-code-plugins/commit/3ad18491a1fc44aaa4b4d92b0f7f6299f3db61cd))

### Merge

- Worktree-bead-CCP-2vo.7([241f664](https://github.com/sussdorff/claude-code-plugins/commit/241f6641a2d88acae4e86a3304b810709cff84d2))
- Worktree-bead-CCP-2vo.8([61635a6](https://github.com/sussdorff/claude-code-plugins/commit/61635a6a5326d798b1ab0be83801c21cd90e51b4))

### Task

- **CCP-2vo.8**: Add validation infrastructure — canonical beads, sibling dispatch, retrospective template([428d46d](https://github.com/sussdorff/claude-code-plugins/commit/428d46d5b7cab48a0321b2a15f8dcdba5b4b7708))
## [2026.04.59] - 2026-04-20

### Miscellaneous

- Sync issues.jsonl bead state([5c27cac](https://github.com/sussdorff/claude-code-plugins/commit/5c27cac56b0c86a64cfa86f617ab090dd91934bd))
- Sync issues.jsonl bead state (close CCP-2vo.7)([712ea8e](https://github.com/sussdorff/claude-code-plugins/commit/712ea8ee40086e30c3fb82ab36471c4121370815))

### Merge

- Worktree-bead-CCP-2vo.7([0cacc83](https://github.com/sussdorff/claude-code-plugins/commit/0cacc832a2c7d966aa668335c7bd90a4e98709de))
## [2026.04.58] - 2026-04-20

### Bug Fixes

- **CCP-c2p**: Address review findings iteration 1 — hermetic tests + stronger evidence scope([c0b1013](https://github.com/sussdorff/claude-code-plugins/commit/c0b101384239f1829baaaf3e6c890cf6020d9f17))
- **CCP-c2p**: Address review findings iteration 2 — honest evidence scope (Option B)([07b11c9](https://github.com/sussdorff/claude-code-plugins/commit/07b11c946042ce1061e23152629807a85a259006))

### Features

- **CCP-c2p**: Green — 3 pilot skills synced; openai.yaml metadata; decisions locked; evidence captured([c6dab53](https://github.com/sussdorff/claude-code-plugins/commit/c6dab53bf5598ff30cc569e6fb167d7aa201589f))

### Miscellaneous

- **beads**: Sync issues.jsonl state([7de88a4](https://github.com/sussdorff/claude-code-plugins/commit/7de88a48a7a3012c2f08f8e3b1c1800dc7b65dfd))
- **beads**: Sync issues.jsonl state([13e7647](https://github.com/sussdorff/claude-code-plugins/commit/13e76470c2595756001ac27532c2a82579b05142))

### Testing

- **CCP-c2p**: Red — pilot skill surface, sync, evidence, decisions([fdaeb2d](https://github.com/sussdorff/claude-code-plugins/commit/fdaeb2d15218f5dfa04186955056d64b3c518a01))

### Merge

- Worktree-bead-CCP-c2p([4fa6dc1](https://github.com/sussdorff/claude-code-plugins/commit/4fa6dc149ff6f1180d6ca25d2bb87e80ca2e3051))

### Task

- **CCP-2vo.7**: Add auto-decisions + token breakdown to Phase 7 learnings report([e3bbac6](https://github.com/sussdorff/claude-code-plugins/commit/e3bbac68a13894929765e7450f4e95401d8ec014))
## [2026.04.57] - 2026-04-20

### Miscellaneous

- Update changelog([216a4a1](https://github.com/sussdorff/claude-code-plugins/commit/216a4a15f18293f00f82d94ac2763b50820b8dfb))
- Sync issues.jsonl bead state([0d5cce5](https://github.com/sussdorff/claude-code-plugins/commit/0d5cce55f0696b149fa61f9dd88e6522b4689736))
- Update changelog([3d9ae11](https://github.com/sussdorff/claude-code-plugins/commit/3d9ae112a84db7b7006fb2f23ef24228034f6d63))

### Merge

- Worktree-bead-CCP-2vo.5([308c8f4](https://github.com/sussdorff/claude-code-plugins/commit/308c8f497db8368c625eec4df37a7b1a447681fa))
## [2026.04.56] - 2026-04-20

### Bug Fixes

- **CCP-2vo.5**: Agent_calls from metrics.db, idempotent stall notes([7f86f87](https://github.com/sussdorff/claude-code-plugins/commit/7f86f87ca154a6da18d977b53037a0abe7c17b2b))
- **CCP-2vo.5**: Epoch-second sqlite comparison, temp-file stall idempotency([0ebdc83](https://github.com/sussdorff/claude-code-plugins/commit/0ebdc83faed98b11707c7ccc35323a53c6320323))
- **CCP-2vo.6**: Address codex adversarial findings — LAST_SHA, RUN_ID fallback, phase2 metrics([eb21ac3](https://github.com/sussdorff/claude-code-plugins/commit/eb21ac393e4f5596009701ee4e57b9f9ebcc9d69))

### Miscellaneous

- **CCP-2vo.6**: Migrate quick-fix to codex-exec.sh, fix session-close handoff([c56add9](https://github.com/sussdorff/claude-code-plugins/commit/c56add9ecebce1c55ff0b895609734586d82c90f))
- Sync issues.jsonl bead state([ab5b092](https://github.com/sussdorff/claude-code-plugins/commit/ab5b09232fb55e59f021571d7a0cf8fbceb23cb1))

### Task

- **CCP-2vo.5**: Wave-orchestrator 1-pane budget + stall detection([14f4682](https://github.com/sussdorff/claude-code-plugins/commit/14f4682fabf32fb3b9fbab01b2d5c6a46abd812c))
## [2026.04.55] - 2026-04-20

### Bug Fixes

- **CCP-2vo.4**: Address review findings — stale phase refs in frontmatter, error table, constraints([6b720ab](https://github.com/sussdorff/claude-code-plugins/commit/6b720abc0119025a0fb2503c85d03bd0274621d4))

### Features

- **CCP-2vo.4**: Rewrite bead-orchestrator flat 0-16, single-pane, inline Codex via codex-exec.sh([00058af](https://github.com/sussdorff/claude-code-plugins/commit/00058af2bd8d2289d8f2c1ea5bf38e67fd1e40db))

### Miscellaneous

- Sync issues.jsonl bead state([2773be1](https://github.com/sussdorff/claude-code-plugins/commit/2773be1ed004de9fca1f1a1d5a546ebcc31dedb8))
- Sync issues.jsonl bead state([1f356a1](https://github.com/sussdorff/claude-code-plugins/commit/1f356a1f877e902cd86aeb937e00e21302ac59ff))
- Sync issues.jsonl bead state([263d630](https://github.com/sussdorff/claude-code-plugins/commit/263d630299a5eefc1e171409c6a92e0ce1546ec5))

### Testing

- **CCP-2vo.4**: Add forced-path fixture specs A/B/C/D for flat 0-16 orchestrator([b61d80a](https://github.com/sussdorff/claude-code-plugins/commit/b61d80aabce8cc66217f74c54c5b5b112c0c73f0))

### Merge

- Worktree-bead-CCP-2vo.4([366088d](https://github.com/sussdorff/claude-code-plugins/commit/366088d88561fcbe33d2b97403d1ed84256bd561))
## [2026.04.54] - 2026-04-20

### Miscellaneous

- Sync issues.jsonl bead state([9828700](https://github.com/sussdorff/claude-code-plugins/commit/98287000420592aa155385b1bfaa79825eae35ee))

### Merge

- Worktree-bead-CCP-2vo.9([bb90232](https://github.com/sussdorff/claude-code-plugins/commit/bb902322ba5085b3ca2faab120f8472ed5fc84fa))
## [2026.04.53] - 2026-04-20

### Miscellaneous

- **beads**: Sync issues.jsonl state([b884f2f](https://github.com/sussdorff/claude-code-plugins/commit/b884f2f10a4938f039e3219120e6ab5833fb74fe))

### Merge

- Worktree-bead-CCP-tkd([b1a138e](https://github.com/sussdorff/claude-code-plugins/commit/b1a138e5e162421d7cd41c5e4722c9599c62274b))
## [2026.04.52] - 2026-04-20

### Bug Fixes

- **CCP-2vo.9**: Address review findings iteration 1([9928b26](https://github.com/sussdorff/claude-code-plugins/commit/9928b265afdb10de1453c98f74d12947e827f185))
- **CCP-2vo.9**: Address review findings iteration 2([0780295](https://github.com/sussdorff/claude-code-plugins/commit/07802959c21b0a44427e88833211ac183c2ce29c))
- **CCP-2vo.9**: Cmux review iter 1 — VETO integrity, docs state consistency, empty provenance normalization([7716a64](https://github.com/sussdorff/claude-code-plugins/commit/7716a64a593d052acc38671db0c60b33d998b63b))
- **CCP-2vo.9**: Cmux review iter 2 — missing-file fixability: human → auto([9f20aae](https://github.com/sussdorff/claude-code-plugins/commit/9f20aaead29ab6614170243cdd2a569ac83ece56))
- **CCP-tkd**: Address review findings iteration 1([22199cd](https://github.com/sussdorff/claude-code-plugins/commit/22199cd0c720e628ef5cedbd6f353e2e6ba9d980))
- **CCP-tkd**: Address review findings iteration 2 — polish([b086ae8](https://github.com/sussdorff/claude-code-plugins/commit/b086ae857384b2c2b81b4126aa5ecd5c81aaa013))
- **CCP-tkd**: Update test_skill_structure to reflect portability split (adapter owns argument-hint)([b91bc71](https://github.com/sussdorff/claude-code-plugins/commit/b91bc7170597e4ce6ecf1692f5dcfa15c608c089))
- **CCP-tkd**: Restore runtime frontmatter (model, disable-model-invocation) to spec-developer SKILL.md([5997fa5](https://github.com/sussdorff/claude-code-plugins/commit/5997fa5a9dabdab283fc812241deec1030a2611a))
- **CCP-tkd**: Remove Claude tool name leaks from portable cores; add Rule 6 + test patterns (F3)([01cc5dc](https://github.com/sussdorff/claude-code-plugins/commit/01cc5dc2ff2d2ad68207a97f56981c504c217f98))
- **CCP-2vo.3**: Normalize model name for rollup + capture python exit code([c615c44](https://github.com/sussdorff/claude-code-plugins/commit/c615c442e52561464a6ff16809de0c7b3e95418f))
- **CCP-2vo.3**: Use additive total_tokens formula + capture reasoning_output_tokens([10d4693](https://github.com/sussdorff/claude-code-plugins/commit/10d469337b6417a21a614de59925f30699da4d7b))

### Features

- **CCP-2vo.9**: Green — add Provenance Compliance Checks, upgrade model to opus([4a87bf1](https://github.com/sussdorff/claude-code-plugins/commit/4a87bf1c52113bc729d4c023371d0a20e61b336c))
- **CCP-tkd**: Green — extract portable skill cores + Claude harness adapters([9c4e5ca](https://github.com/sussdorff/claude-code-plugins/commit/9c4e5ca39252a19668e87021a992a23ec9e6bee1))

### Testing

- **CCP-2vo.9**: Red — TestModelUpgrade, TestVetoChecks, TestAdvisoryCheck, TestOutputFormatUpdated, TestInformationBarriersUpdated([7557787](https://github.com/sussdorff/claude-code-plugins/commit/7557787af4f1b7b2733615bf89f547bfbe75dda2))
- **CCP-tkd**: Red — portability split assertions for 3 pilot skills([133e53d](https://github.com/sussdorff/claude-code-plugins/commit/133e53d8154546c0a2b9e4787f1447254e7cfc79))

### Merge

- Worktree-bead-CCP-2vo.3([3b7c2a2](https://github.com/sussdorff/claude-code-plugins/commit/3b7c2a2b0a8738945121763ed72e89309625bca1))

### Task

- **CCP-2vo.3**: Add codex-exec.sh wrapper with turn.completed token capture([a520b89](https://github.com/sussdorff/claude-code-plugins/commit/a520b896f1739307ff41eb462537cbf4f8fbaa63))
## [2026.04.51] - 2026-04-20

### Merge

- Bring in origin/main (first merge — resolve metrics.py import conflict)([e55fbbf](https://github.com/sussdorff/claude-code-plugins/commit/e55fbbf673227bd09b68e4237aae7b070f257fca))
- Worktree-bead-CCP-2vo.1([6b7feee](https://github.com/sussdorff/claude-code-plugins/commit/6b7feee3fc4d3bfec203713d278c430cd2df84e4))
## [2026.04.50] - 2026-04-20

### Miscellaneous

- **beads**: Sync issues.jsonl with main branch state([9f01761](https://github.com/sussdorff/claude-code-plugins/commit/9f017614607f7328ca285c6221d7abec5f99f206))

### Merge

- Worktree-bead-CCP-u01([ddd629a](https://github.com/sussdorff/claude-code-plugins/commit/ddd629a0d6ffbdcb43175a872dcd5f21d122a2c8))
## [2026.04.49] - 2026-04-20

### Bug Fixes

- **CCP-2vo.1**: Address review findings iteration 1([56e352d](https://github.com/sussdorff/claude-code-plugins/commit/56e352d90023767e0f98060d1260d7c19bdf77bd))
- **CCP-2vo.1**: Address review findings iteration 2([47e9d09](https://github.com/sussdorff/claude-code-plugins/commit/47e9d09a22e8e69d9e2792b6bf6b0adda9e68fdd))
- **CCP-2vo.1**: Harden verification token capture against special chars([3922ad3](https://github.com/sussdorff/claude-code-plugins/commit/3922ad3c9db517ef25d5261970bd715d7f83f21c))
- **CCP-2vo.2**: Thread run_id through insert_bead_run, upsert_ccusage_row, update_phase2_metrics([b626f59](https://github.com/sussdorff/claude-code-plugins/commit/b626f595e8e5fbc21cc25a3ff2a1bccb269d74f5))
- **CCP-u01**: Guard empty skills tokens and fatal-error on missing sources([8422ed3](https://github.com/sussdorff/claude-code-plugins/commit/8422ed33070fcce71bedd5fde477f16834bda224))
- **CCP-u01**: Restore issues.jsonl to pre-implementation snapshot([9024f39](https://github.com/sussdorff/claude-code-plugins/commit/9024f39fd81e28cb6b29a4e9e930c56faa46225c))

### Documentation

- **codex-skills**: Align rollout plan with machine-state and refined wave([2cade51](https://github.com/sussdorff/claude-code-plugins/commit/2cade5126d0cafc0bf6823cd98568348cc351704))

### Features

- **metrics**: Backfill_codex.py retroactive Codex attribution tool([194e391](https://github.com/sussdorff/claude-code-plugins/commit/194e391edaf85dbf96045b6f548d3fa3942ff008))
- **CCP-2vo.1**: Fix verification_tokens silent-fail + provenance contract([762af47](https://github.com/sussdorff/claude-code-plugins/commit/762af47af0ee8f336ce20cd9320929263142f64e))
- **CCP-2vo.2**: Add run_id identity, agent_calls table, Python insert API([b506cc7](https://github.com/sussdorff/claude-code-plugins/commit/b506cc73c1447f24da35999f5229b0048a9e77bb))
- **CCP-u01**: Add sync-codex-skills script with --check and --user modes([539ff42](https://github.com/sussdorff/claude-code-plugins/commit/539ff42c53c3d8af4b99d49a908a4d081cea1deb))

### Miscellaneous

- **beads**: Untrack .beads/issues.jsonl — Dolt is canonical([e2dea75](https://github.com/sussdorff/claude-code-plugins/commit/e2dea751537de6bea14196daa9339b96f3747204))
- Update changelog and bump version to 2026.04.49([4a7b33f](https://github.com/sussdorff/claude-code-plugins/commit/4a7b33fa29ee1047479acd0aff2f79f114af2ff1))

### Testing

- **CCP-2vo.1**: Red — verification provenance contract([47cb9e5](https://github.com/sussdorff/claude-code-plugins/commit/47cb9e56befc2a081ccc391c2e0b561268652910))
## [2026.04.47] - 2026-04-20

### Features

- **agents**: Add Step 16a pipeline watch to session-close([cad9746](https://github.com/sussdorff/claude-code-plugins/commit/cad97460ea4d37b460c9e29fc0fb7c5b3a877207))
- **agents**: Distinguish no-workflow from no-run-registered in pipeline watch([f06cbbd](https://github.com/sussdorff/claude-code-plugins/commit/f06cbbdb493416c88e6dd70a6206020cbf5c726e))
- **metrics**: Ingest Claude Code + Codex tokens via ccusage([12a62ff](https://github.com/sussdorff/claude-code-plugins/commit/12a62ffff1f994615ceb7996ab4a2f4b1529a6db))

### Miscellaneous

- Update changelog([d084101](https://github.com/sussdorff/claude-code-plugins/commit/d0841012c0a695b1e49cd4eac0e4643e5c724fcf))

### Refactoring

- **agents**: Extract turn-log/merge handlers from session-close([e562960](https://github.com/sussdorff/claude-code-plugins/commit/e56296022ddc498915ab45f88e2c326e2ed36104))
## [2026.04.46] - 2026-04-20

### Features

- **skills**: Add wave-reviewer skill([7c67576](https://github.com/sussdorff/claude-code-plugins/commit/7c6757665658ee5b4aed67f37fd6f3994656a5bc))

### Miscellaneous

- **skills**: Tighten wave-reviewer structure([ee15ee9](https://github.com/sussdorff/claude-code-plugins/commit/ee15ee95e8825c847feed5426f1c5a6cf3a7dec4))
- **skills**: Polish wave-reviewer structure (advisory fixes)([8fb2961](https://github.com/sussdorff/claude-code-plugins/commit/8fb296100c62c4cdccbbd672dc01d0f3de0374b5))
## [2026.04.45] - 2026-04-20

### Miscellaneous

- Update changelog([f128243](https://github.com/sussdorff/claude-code-plugins/commit/f128243d68c9c03ce9bf7102a35fc2bd27a99608))
- **beads**: Sync bead state — wave 1+2a complete, vision skill chain unblocked([ae8be96](https://github.com/sussdorff/claude-code-plugins/commit/ae8be9615dcb28071c0c248623c61b1097cfb414))
- Update changelog([aa7ec14](https://github.com/sussdorff/claude-code-plugins/commit/aa7ec1460526bfe8d322986cd930d2e88522fd39))
## [2026.04.44] - 2026-04-19

### Bug Fixes

- **CCP-xpr**: Address review findings iteration 1([ab13ff2](https://github.com/sussdorff/claude-code-plugins/commit/ab13ff23cc429c762b97f2cecf61bf7090202385))
- **CCP-xpr**: Address review findings iteration 2([51aaf92](https://github.com/sussdorff/claude-code-plugins/commit/51aaf92cbd9703b520e071fe88ab9554dda8fbc8))
- **CCP-xpr**: Address review findings iteration 3([d189e9e](https://github.com/sussdorff/claude-code-plugins/commit/d189e9efc5c570ffd51d7e8b7de1c434b7ba9414))

### Features

- **CCP-xpr**: Green — implement vision_parser module([91d7a7d](https://github.com/sussdorff/claude-code-plugins/commit/91d7a7d1e7b52638fb5906ad1a9a3c25c49e502d))

### Miscellaneous

- Sync bead state([3bff177](https://github.com/sussdorff/claude-code-plugins/commit/3bff1776beab75356eb137e39336937cd5cd8d8d))
- Sync bead state for CCP-xpr session close([4d8686e](https://github.com/sussdorff/claude-code-plugins/commit/4d8686eb9ac32be788838e8bfa538f5e4220c6f9))

### Testing

- **CCP-xpr**: Red — vision_parser tests + fixtures([a46ff84](https://github.com/sussdorff/claude-code-plugins/commit/a46ff84bcf58f51ea5a1d072c5354ae7d432bcc9))

### Merge

- Worktree-bead-CCP-xpr([865df9d](https://github.com/sussdorff/claude-code-plugins/commit/865df9dcdc7853c98c44fa312d057966ecf9ce53))
## [2026.04.43] - 2026-04-19

### Bug Fixes

- **CCP-qrg**: Address Codex review regressions in bd-wrapper and installer([45ca9c1](https://github.com/sussdorff/claude-code-plugins/commit/45ca9c1e8446c19a57a19676fb7181ce9d838df8))
- **CCP-qrg**: Detect and skip other bd-wrapper copies in PATH walk to prevent exec loop([370b0ce](https://github.com/sussdorff/claude-code-plugins/commit/370b0cebc48e37a709978fe6c7f848f8539ef36a))
- **CCP-qrg**: Address review findings iteration 1([276433f](https://github.com/sussdorff/claude-code-plugins/commit/276433f5ccdaa0b977f23c6c1b5f81142816bb96))

### Features

- **CCP-qrg**: Add PATH-shim bd wrapper so bd lint --check=architecture-contracts works without sourcing shell extension([4adbe26](https://github.com/sussdorff/claude-code-plugins/commit/4adbe262e139c30c7a10f381014cdf7a03471381))

### Miscellaneous

- Sync bead state([d4a0f85](https://github.com/sussdorff/claude-code-plugins/commit/d4a0f8514e42ff37b3482797b31e3a2376644d52))
- **CCP-qrg**: Sync bead state([f57cbc7](https://github.com/sussdorff/claude-code-plugins/commit/f57cbc768f593cee9f4b92d58b2c6eba8167d207))
- **CCP-qrg**: Sync bead state([a3fa0ce](https://github.com/sussdorff/claude-code-plugins/commit/a3fa0ce5cfccf7a61a93b144ab9c02377e49f0bf))
- **CCP-qrg**: Update issues.jsonl bead state([b3b93cd](https://github.com/sussdorff/claude-code-plugins/commit/b3b93cd526ad12a97b4646b479e8ecb288135122))
- **CCP-qrg**: Update issues.jsonl bead state([50ee60e](https://github.com/sussdorff/claude-code-plugins/commit/50ee60e40cef541b3af15cd90a929894076b7c1a))
- Final issues.jsonl sync([4c5a411](https://github.com/sussdorff/claude-code-plugins/commit/4c5a4113197a73c6fcce80ada73a53354be3262b))

### Merge

- Worktree-bead-CCP-qrg([58b3c20](https://github.com/sussdorff/claude-code-plugins/commit/58b3c209feff9c690921f39c06cde2b43fa3a907))
## [2026.04.42] - 2026-04-19

### Bug Fixes

- **CCP-2q2**: Handle quoted document_type and skip fenced code blocks in tense-gate([f3018fe](https://github.com/sussdorff/claude-code-plugins/commit/f3018fe42269bc0c9c0fd9d7003d72a3089764fe))

### Miscellaneous

- **beads**: Sync bead state before CCP-2q2 merge([f53b976](https://github.com/sussdorff/claude-code-plugins/commit/f53b9763e48adfdbc0d7f778c5356c5b1f112f46))
- **beads**: Sync bead state for CCP-2q2 session([ff9b0cc](https://github.com/sussdorff/claude-code-plugins/commit/ff9b0cc91b6470da4190f150defcf85579977b1b))
- **beads**: Sync issues.jsonl export([23aae6f](https://github.com/sussdorff/claude-code-plugins/commit/23aae6f12ad8ac7dd5afae60e66aaf31e499734b))

### Merge

- Worktree-bead-CCP-2q2([0809281](https://github.com/sussdorff/claude-code-plugins/commit/08092813238ed3386ec73e5ba82481ef81221e10))

### Task

- **CCP-2q2**: Add tense-gate lint script for prescriptive-present enforcement([0fec1f1](https://github.com/sussdorff/claude-code-plugins/commit/0fec1f1cca0a615063cea88c6d364dc32097b658))
## [2026.04.41] - 2026-04-19

### Features

- **CCP-9yh**: Enforce mutual exclusion of None with gap markers in bd-lint-contracts([f93254c](https://github.com/sussdorff/claude-code-plugins/commit/f93254c2604e6c7dfe3a03b756b793b1ce057ded))

### Miscellaneous

- **beads**: Sync bead state — Trinity waves 1-3, vision skills, CCP-w56 superseded([0c38363](https://github.com/sussdorff/claude-code-plugins/commit/0c383632edcbc788ce6fd7b6a0b92491975b259e))
- **beads**: Sync bead state before CCP-9yh merge([fa815d9](https://github.com/sussdorff/claude-code-plugins/commit/fa815d9e2dd5a64d1a350d7d2787535db87eebf0))
- **beads**: Sync bead state for CCP-9yh session([d5b0dab](https://github.com/sussdorff/claude-code-plugins/commit/d5b0dab3aff508c58acf13cf1bddf882efcde287))

### Merge

- Worktree-bead-CCP-9yh([53ddde6](https://github.com/sussdorff/claude-code-plugins/commit/53ddde6373e52697df9d0733571f54d1874c104e))
## [2026.04.40] - 2026-04-19

### Miscellaneous

- **CCP-uy2**: Sync bead state and remove stale issues.jsonl symlink([8339819](https://github.com/sussdorff/claude-code-plugins/commit/8339819ff5af4d9584f3c475ca4b9e11746f16f1))
- **CCP-uy2**: Remove issues.jsonl from git tracking([299e12e](https://github.com/sussdorff/claude-code-plugins/commit/299e12eba3ea7c656323c1cc0d39f69d885062f1))

### Merge

- Worktree-bead-CCP-uy2([ceb61e5](https://github.com/sussdorff/claude-code-plugins/commit/ceb61e5785abc25295bf88ed35fdc6cbd911fd4e))
## [2026.04.39] - 2026-04-19

### Merge

- Resolve conflicts from origin/main for CCP-2hd([90f5474](https://github.com/sussdorff/claude-code-plugins/commit/90f54741345ad84b817a0cbda72bd5740e4a7be9))
- Worktree-bead-CCP-2hd([2a6b809](https://github.com/sussdorff/claude-code-plugins/commit/2a6b80956eef32bf97da8d9b1e863fdf2b18c6a8))
## [2026.04.38] - 2026-04-19

### Bug Fixes

- **CCP-uy2**: Address review findings iteration 1([7369199](https://github.com/sussdorff/claude-code-plugins/commit/7369199542186112e0b88a4439c0c01392e3a331))
- **CCP-uy2**: Address review findings iteration 2([181ff7c](https://github.com/sussdorff/claude-code-plugins/commit/181ff7c76fdd4e6b4775f93e8e011f3767b9057b))
- **CCP-uy2**: Fix 3 regressions from adversarial review + 4 new tests([4515ef9](https://github.com/sussdorff/claude-code-plugins/commit/4515ef9bce6564b79a7131b75fee7030a4d7c1f9))
- **CCP-2hd**: Update tests and golden file to match new full-trinity fixture state([9638859](https://github.com/sussdorff/claude-code-plugins/commit/96388597c0517e9d750bfcef959307771191c08d))
- **CCP-2hd**: Address review findings iteration 1([8bab326](https://github.com/sussdorff/claude-code-plugins/commit/8bab326ab7987aa920e9b270b9f675ff03fb77f7))
- **CCP-2hd**: Address review findings iteration 2 — fix line numbers, ADR status, vision grep pattern, conformance_skip passthrough([6b87139](https://github.com/sussdorff/claude-code-plugins/commit/6b87139ca489ca800c73f92576a0152c77a673a0))
- **CCP-2hd**: Add per-package matrix axis and fix epic-init scout timing/gate-mode([2191819](https://github.com/sussdorff/claude-code-plugins/commit/2191819599def3729bbd05ee0e7b87909bbe750a))
- **CCP-2hd**: Strict touched_paths scoping for vision boundary + move scout to Phase 4([772654f](https://github.com/sussdorff/claude-code-plugins/commit/772654f7ec63d714d60a1a02aefdd289958cd18a))
- **CCP-0ql**: Fix bead-dropping and timezone bugs in wave-status.sh([1f987c0](https://github.com/sussdorff/claude-code-plugins/commit/1f987c033e20ac48e806500a52f2105ae6b9a1b1))

### Documentation

- **CCP-uy2**: Update architecture-trinity README with feature docs([e3885b2](https://github.com/sussdorff/claude-code-plugins/commit/e3885b2482f03a4e361e1539c0a420ae607b5ee6))

### Features

- **CCP-uy2**: Green — implement adr-hoist-check.py([5f97755](https://github.com/sussdorff/claude-code-plugins/commit/5f97755fe8e4a2c29f0867692020275b65d73c6b))
- **CCP-uy2**: Add /adr-gap skill, SKILL.md, adr-gap.sh, and adr-frontmatter.md reference([95c84d0](https://github.com/sussdorff/claude-code-plugins/commit/95c84d0140797fca5e60306746500fb9a44122c3))
- **CCP-2hd**: Add architecture-scout agent definition with coverage matrix output([a98254b](https://github.com/sussdorff/claude-code-plugins/commit/a98254b9d9dd8a5cefb4ab09f3c1229e4b551452))
- **CCP-2hd**: Add example-matrix reference for architecture-scout([bf38c14](https://github.com/sussdorff/claude-code-plugins/commit/bf38c14e12efc33ff34acf0f9696b720d37ffead))
- **CCP-2hd**: Extend mira-adapters fixture for architecture-scout test scenarios([eac25c3](https://github.com/sussdorff/claude-code-plugins/commit/eac25c3ee22defcbf9226871a95e6f247b0dbacb))
- **CCP-2hd**: Integrate architecture-scout into /plan and /epic-init skills([039de1f](https://github.com/sussdorff/claude-code-plugins/commit/039de1f36b727806c70fa10f6085774706431cf3))

### Miscellaneous

- **CCP-uy2**: Untrack issues.jsonl (gitignored)([8edc0cf](https://github.com/sussdorff/claude-code-plugins/commit/8edc0cf357f83c9bf91b71083454befdc1e22d03))
- Sync bead state([bd4ea89](https://github.com/sussdorff/claude-code-plugins/commit/bd4ea897a2dbc28c492df04aa56b16f06b4dacff))
- Sync bead state for CCP-0ql([0b278a3](https://github.com/sussdorff/claude-code-plugins/commit/0b278a30e76ec240a29e44bd42b20c8a2bafcfbc))

### Testing

- **CCP-uy2**: Red — failing tests for adr-hoist-check.py([73b13d3](https://github.com/sussdorff/claude-code-plugins/commit/73b13d36336d6d51244d29085577c5de1c5fa9f7))

### Merge

- Worktree-bead-CCP-0ql([56f30c4](https://github.com/sussdorff/claude-code-plugins/commit/56f30c459acc956ebd657c51eb961361b45bdd82))
## [2026.04.37] - 2026-04-19

### Miscellaneous

- Sync bead state after merge resolution([5de92b2](https://github.com/sussdorff/claude-code-plugins/commit/5de92b2d0408c496ddfd208c29cdf4b19fa226f7))
- Remove issues.jsonl from git tracking (gitignored)([5949708](https://github.com/sussdorff/claude-code-plugins/commit/594970895ba3918cc9037849fde080b8f6500a50))

### Merge

- Resolve conflicts from origin/main for CCP-0hr([dd3eaf1](https://github.com/sussdorff/claude-code-plugins/commit/dd3eaf14138bd4a50fa201b86167d80923b5eb51))
- Worktree-bead-CCP-0hr([b2dc863](https://github.com/sussdorff/claude-code-plugins/commit/b2dc8636c6710bf57e7b61464f671d2f344ab797))
## [2026.04.36] - 2026-04-19

### Documentation

- **wave-orchestrator**: Align monitoring to 270s cache-warm poll cadence([85812ad](https://github.com/sussdorff/claude-code-plugins/commit/85812ad3729d4b62766d4507bd66e4cd83174e34))

### Features

- **CCP-0hr**: Green — bd_lint_contracts.py linter (stdlib, 30 tests pass)([978d577](https://github.com/sussdorff/claude-code-plugins/commit/978d577a56c154b56ecef7459a8dea26349ca4db))
- **CCP-0hr**: Shell wrapper bd-lint-extension.sh for bd lint --check=architecture-contracts([5a72d8d](https://github.com/sussdorff/claude-code-plugins/commit/5a72d8dc76428cdbf9654885e8f76961ce919047))
- **CCP-0hr**: Update create SKILL.md with Phase 3.5 contract-label check and Phase 4.5 smoke-check([f789651](https://github.com/sussdorff/claude-code-plugins/commit/f789651e22722b93891e88806b603a69f71310e4))
- **CCP-0hr**: Add contract-sections.md reference documentation([4bf8057](https://github.com/sussdorff/claude-code-plugins/commit/4bf8057caf308c0473c0dc5e1c088e38d7d1a0a2))
## [2026.04.35] - 2026-04-19

### Bug Fixes

- **CCP-0hr**: Address review findings iteration 1([cb361d8](https://github.com/sussdorff/claude-code-plugins/commit/cb361d86680a21fc5230ca5628938c5d55f883e7))
- **CCP-0hr**: Address review findings iteration 2 — fence-strip in validate, bd-unavailable exit-1, untrack issues.jsonl([f2e0e0c](https://github.com/sussdorff/claude-code-plugins/commit/f2e0e0c6333d46c93d09540a237a0eb5538c938c))
- **CCP-0hr**: Address review findings iteration 1 (phase2)([7707e6b](https://github.com/sussdorff/claude-code-plugins/commit/7707e6b6cc57feaf8b2d5a0c0c0bb597e40f0429))
- **CCP-0hr**: Address review findings iteration 2 (phase2) — require description after NEEDED markers([3a8753f](https://github.com/sussdorff/claude-code-plugins/commit/3a8753f0902f96ec2f314c3a9d4743c367af38c7))
- **CCP-vwg**: Address review findings iteration 1([7a3589a](https://github.com/sussdorff/claude-code-plugins/commit/7a3589a70fa6a6c7bda02f69ca33a77600518f82))
- **CCP-vwg**: Address review findings iteration 2([9644a28](https://github.com/sussdorff/claude-code-plugins/commit/9644a28e54ab237fcc964cde4fab699e49fa41b8))
- **CCP-vwg**: Address review findings iteration 2([220aeac](https://github.com/sussdorff/claude-code-plugins/commit/220aeace9167e9bfefe2d47f77e38ef81eaa75ed))
- **CCP-vwg**: Address review findings iteration 3 — inline-list comment ordering and false-pass test([354a176](https://github.com/sussdorff/claude-code-plugins/commit/354a176c67b3222c3588f8acf0f48479f26a052c))

### Features

- **CCP-0hr**: Green — bd-lint-contracts linter + shell extension + skill + docs([5af1d61](https://github.com/sussdorff/claude-code-plugins/commit/5af1d6189915fa000591f71f6cc860d9053fe9a0))
- **CCP-vwg**: Green — enforcement matrix scanner, fixtures, SKILL.md update([685c3e8](https://github.com/sussdorff/claude-code-plugins/commit/685c3e8d3344bc580b4189a335a0578dcdf8bddd))

### Miscellaneous

- **CCP-0hr**: Untrack issues.jsonl (covered by .gitignore)([f3456f7](https://github.com/sussdorff/claude-code-plugins/commit/f3456f7f2ffaf57448387350bfb7e22454fe67d1))
- **CCP-0hr**: Untrack root issues.jsonl from git index([f14d063](https://github.com/sussdorff/claude-code-plugins/commit/f14d063cfb5ee00d928c326380f37ae110b01a2c))
- **CCP-vwg**: Remove issues.jsonl from tracking (gitignore)([6522fc8](https://github.com/sussdorff/claude-code-plugins/commit/6522fc81bcbd0d43a8d31e1865abd168130ca524))
- **CCP-vwg**: Update bead state and untrack issues.jsonl([dfe732c](https://github.com/sussdorff/claude-code-plugins/commit/dfe732ca9624ef48c72df71b1b4452e0d289520c))
- Untrack issues.jsonl (covered by .gitignore)([512847b](https://github.com/sussdorff/claude-code-plugins/commit/512847b6f99a52856e599cd6b5a561ae4d850238))

### Testing

- **CCP-0hr**: Red — fixture-based test suite for bd-lint-contracts([63af3c3](https://github.com/sussdorff/claude-code-plugins/commit/63af3c34e02ca1603feaafce83488435547ed2eb))
- **CCP-0hr**: Red — fixture-based test suite for bd-lint-contracts([dfe75b3](https://github.com/sussdorff/claude-code-plugins/commit/dfe75b36358c01004a1f01cb26c23bb5f88b9020))
- **CCP-vwg**: Red — enforcement matrix tests (all failing, scanner not yet created)([aa78a3a](https://github.com/sussdorff/claude-code-plugins/commit/aa78a3a3fc754c92dd929088e60f56612c480efb))

### Merge

- Worktree-bead-CCP-vwg([2f9c25b](https://github.com/sussdorff/claude-code-plugins/commit/2f9c25b4ef74779a4ccffb5f8f0f1bf3a76c82b6))
## [2026.04.34] - 2026-04-19

### Bug Fixes

- **CCP-089**: Remove duplicate issues.jsonl from tracking([75b2bab](https://github.com/sussdorff/claude-code-plugins/commit/75b2bab7514f6c5ea635f2868dd41dd591c7c11f))
- **CCP-089**: Align summary text to four-term vocabulary (advisory)([0975131](https://github.com/sussdorff/claude-code-plugins/commit/0975131c91b74dd087e990390482a57b8540f6bf))

### Miscellaneous

- Update changelog([fc41a1c](https://github.com/sussdorff/claude-code-plugins/commit/fc41a1c9e404180517b7fc8cb617eb229f728295))
- **CCP-089**: Update bead status to in_progress([f7b81a1](https://github.com/sussdorff/claude-code-plugins/commit/f7b81a15c03117eb1295a0febb282be07c0d4f70))
- **CCP-089**: Introduce Architecture Trinity vocabulary in docs([c038bdb](https://github.com/sussdorff/claude-code-plugins/commit/c038bdb271c9ceb5c8a661bad4f10c94b783a82b))
- Remove issues.jsonl from tracking (covered by .gitignore)([f12ce18](https://github.com/sussdorff/claude-code-plugins/commit/f12ce18e303e725d1f720d7e988e0a6ab9592dfb))

### Merge

- Resolve conflict from origin/main — keep four-term vocabulary([9f8c794](https://github.com/sussdorff/claude-code-plugins/commit/9f8c7943dc39add7670e42b36d582fcb7d3cf1b4))
- Worktree-bead-CCP-089([d304e0c](https://github.com/sussdorff/claude-code-plugins/commit/d304e0c7803f1ac7901397512c1bca46235af694))
## [2026.04.33] - 2026-04-19

### Features

- **CCP-3oy**: Wire Turn-Log consumer in session-close and worktree-manager([c7a813c](https://github.com/sussdorff/claude-code-plugins/commit/c7a813ce82a05bc5d644924a6a84335ce8c4e835))
- **dev-tools**: Add binary-explorer skill for reverse-engineering desktop apps([5990fac](https://github.com/sussdorff/claude-code-plugins/commit/5990fac0a41c8f6243c37ec99dce60414488dc66))

### Miscellaneous

- **beads**: Create Trinity-Harness epic and 10 subtask beads([9c544f1](https://github.com/sussdorff/claude-code-plugins/commit/9c544f10dbbecdc3deb7f16500565d93574d5d1f))
- **CCP-089**: Introduce Architecture Trinity vocabulary in docs([4211db5](https://github.com/sussdorff/claude-code-plugins/commit/4211db563d1a37be0d0039a5721240ff96f132d6))
- Update changelog([64ddb97](https://github.com/sussdorff/claude-code-plugins/commit/64ddb9740a20f593f01525b7565c04a14d824427))
## [2026.04.32] - 2026-04-16

### Features

- **dev-tools**: Add codex-guide agent for Codex CLI documentation queries([b49b17e](https://github.com/sussdorff/claude-code-plugins/commit/b49b17e3fbe5c7a535c5cb394edaa4fb92efeb41))

### Miscellaneous

- Update changelog([928fbdb](https://github.com/sussdorff/claude-code-plugins/commit/928fbdb075ff4a8f7c063d762c0930d305b5c99f))
## [2026.04.31] - 2026-04-15

### Merge

- Worktree-bead-CCP-a81([0511b61](https://github.com/sussdorff/claude-code-plugins/commit/0511b6108d90c52d35d46404e53defd4057a2e6a))
## [2026.04.30] - 2026-04-15

### Bug Fixes

- **codex**: Switch cmux-reviewer and quick-fix to blocking review invocation([5899a6e](https://github.com/sussdorff/claude-code-plugins/commit/5899a6eec7491d474eae8131523f6a65cf7bdd00))
## [2026.04.29] - 2026-04-15

### Bug Fixes

- **CCP-a81**: Address review findings iteration 1([77d3cca](https://github.com/sussdorff/claude-code-plugins/commit/77d3cca24dc1c67efc3c4197dae5dcabfd3b4281))
- **CCP-a81**: Address review findings iteration 2([24810d3](https://github.com/sussdorff/claude-code-plugins/commit/24810d32e642fdbb8da1630a9bc5419d7e43e3d8))
- **CCP-a81**: Address review findings iteration 3([d12d9c6](https://github.com/sussdorff/claude-code-plugins/commit/d12d9c63f70669fad12e6cad4c59de515b96590f))
- **CCP-a81**: Address review findings iteration 4([13c8e1a](https://github.com/sussdorff/claude-code-plugins/commit/13c8e1a48b9d6a41f2b25bd0aa89ea6fc841873c))

### Documentation

- Add Codex skills rollout plan([4e5def6](https://github.com/sussdorff/claude-code-plugins/commit/4e5def6bd64760046174378afb45be050b3a0dae))
- **dolt**: Document bd v1.0.0 auto-start and update red flags([d11e02b](https://github.com/sussdorff/claude-code-plugins/commit/d11e02bc8ebc183060d533528262740fa03b5401))

### Features

- **CCP-a81**: Green — canonical-catalog detection in council + Phase 6.5 integration-verification([1199258](https://github.com/sussdorff/claude-code-plugins/commit/1199258203cb27587cddbc3f88acf4afec2f78f5))

### Testing

- **CCP-a81**: Red — regression scenario for canonical-catalog and integration-verification gap([43de520](https://github.com/sussdorff/claude-code-plugins/commit/43de5205e6633fae03c895ac526675f8acacf7c5))
## [2026.04.28] - 2026-04-15

### Bug Fixes

- **CCP-nxy**: Guard idle detection against active Claude thinking markers([6e313fe](https://github.com/sussdorff/claude-code-plugins/commit/6e313fef1f7a3cebae2e84dbbb875c84320d049e))
- **CCP-nxy**: Position-based idle detection, guard against stale terminal history([ee8c1c1](https://github.com/sussdorff/claude-code-plugins/commit/ee8c1c1caa31a187869a7b14218d0fac28f2ab5d))
- **CCP-nxy**: Check 2 preceding lines for thinking markers, not just 1([631e0cc](https://github.com/sussdorff/claude-code-plugins/commit/631e0cc5180cc4aec1a21fff4ed76c66ff879dc0))

### Miscellaneous

- Update changelog([b84693c](https://github.com/sussdorff/claude-code-plugins/commit/b84693c6432b629fc3a67777b538added98378f6))

### Merge

- Worktree-bead-CCP-nxy([9c9898c](https://github.com/sussdorff/claude-code-plugins/commit/9c9898c45a6a8f888a039b1953bef165358718a1))
## [2026.04.27] - 2026-04-15

### Bug Fixes

- **CCP-2a2**: Promote Module Impact/Existing Patterns to first-class sections in Codex template; add new-file fallback to Phase 2.6([c6025aa](https://github.com/sussdorff/claude-code-plugins/commit/c6025aa6ef5fa6b33b73e8ce82cc9262d3f73b09))
- **wave-orchestrator**: Detect dead cmux panes via error pattern([e60feda](https://github.com/sussdorff/claude-code-plugins/commit/e60feda7f1985cf4f6d7b25a927bea02e1ef2fc1))
- **quick-fix**: Trigger session-close via Agent tool, not cmux send([4d741c6](https://github.com/sussdorff/claude-code-plugins/commit/4d741c63a6681945ada01a1e64b4a7e69d7da7a2))

### Documentation

- Add project-context.md and refresh README for 8-plugin bundle layout([d615949](https://github.com/sussdorff/claude-code-plugins/commit/d615949675c6874a4678029e8633b52a794fd63a))

### Features

- **CCP-2a2**: Add Phase 2.6 Module Impact Analysis to bead-orchestrator([8daae87](https://github.com/sussdorff/claude-code-plugins/commit/8daae8753e60549f9ad05867611f3699412e3cec))

### Miscellaneous

- **CCP-qo0**: Set project-context skill model to inherit([eb5d2e3](https://github.com/sussdorff/claude-code-plugins/commit/eb5d2e313aaa9bfd6daf95c93e690ae2eb7db2bb))
- **beads-workflow**: Clarify cmux surface detection in quick-fix agent([2049300](https://github.com/sussdorff/claude-code-plugins/commit/20493000f0f2e7d5737022fffee48fd5399f1ec6))
- Update changelog([4f3be56](https://github.com/sussdorff/claude-code-plugins/commit/4f3be5678a67fc71adeef3df08b975124e092e97))
- Update changelog([435ccda](https://github.com/sussdorff/claude-code-plugins/commit/435ccdacfde50d19d5d1a462ba296ee0d9c84b13))

### Merge

- Worktree-bead-CCP-2a2([b1f6e8b](https://github.com/sussdorff/claude-code-plugins/commit/b1f6e8b362782efb8a09777fb5688005407d99a3))
## [2026.04.26] - 2026-04-15

### Miscellaneous

- Update changelog([2e1ed0b](https://github.com/sussdorff/claude-code-plugins/commit/2e1ed0b6fe4e6026a73d9abe3e634a0c0f67f4b2))

### Merge

- Worktree-bead-CCP-qo0([5b571e2](https://github.com/sussdorff/claude-code-plugins/commit/5b571e2b94bf1e9b16f589f5b054d02b3e4b3eca))
## [2026.04.25] - 2026-04-15

### Bug Fixes

- **CCP-1ul**: Add arch context to codex template, use json field for design([16f708d](https://github.com/sussdorff/claude-code-plugins/commit/16f708df0f87f02782aef743ca83fa710a9b32c2))

### Features

- **CCP-qo0**: Green — /project-context skill with output template and plugin registration([7ae639d](https://github.com/sussdorff/claude-code-plugins/commit/7ae639dfd42433c3e0633256a076d1fc3db987fb))
- **CCP-1ul**: Inject project architecture context block into subagent prompt([82724b0](https://github.com/sussdorff/claude-code-plugins/commit/82724b0b0cd0777426f21ad721f25cda5c0b3fff))

### Miscellaneous

- Update changelog([7506c0c](https://github.com/sussdorff/claude-code-plugins/commit/7506c0c714f3d334a0c282a5bc778a322682d42f))

### Testing

- **CCP-qo0**: Red — structural tests for /project-context skill([c5125e0](https://github.com/sussdorff/claude-code-plugins/commit/c5125e0b3ae9b9930394cf0f853fe20364f0fa61))

### Merge

- Worktree-bead-CCP-1ul([80de26e](https://github.com/sussdorff/claude-code-plugins/commit/80de26e4e88b2bd55969930300d3f5430d19c882))
## [2026.04.24] - 2026-04-15

### Bug Fixes

- **CCP-asr**: Replace blind background wait with Monitor-based event loop([c74ef25](https://github.com/sussdorff/claude-code-plugins/commit/c74ef25d0fbcfe30bfeaaee5786ec9ea8f05874e))
- **CCP-asr**: Address Codex review regressions in codex-watch.sh([a703a2b](https://github.com/sussdorff/claude-code-plugins/commit/a703a2b0058fd346a4549ce6d7639426dd6ed557))
- **CCP-asr**: Remove mktemp dep from poll loop to fix locked-down env crash([8ffddbf](https://github.com/sussdorff/claude-code-plugins/commit/8ffddbf47bb551d498e2f28b56385b46a5db390e))
- **CCP-asr**: Restore actionable error reason in CODEX_WATCH_ERROR([dcc2d0c](https://github.com/sussdorff/claude-code-plugins/commit/dcc2d0c0f03c945249e0d3984cf9b00f27136673))

### Miscellaneous

- Update changelog([133186f](https://github.com/sussdorff/claude-code-plugins/commit/133186ff8e6b461b34004d5b84a37a7e31ab2e2a))

### Merge

- Worktree-bead-CCP-asr([430bbb6](https://github.com/sussdorff/claude-code-plugins/commit/430bbb6466610702191b11d04bccd133f7027283))
## [2026.04.23] - 2026-04-15

### Bug Fixes

- **beads-workflow**: Self-locate metrics lib without CLAUDE_PLUGIN_ROOT([42d8788](https://github.com/sussdorff/claude-code-plugins/commit/42d87883b235b6b19321a6bbd0917b60b8439198))
## [2026.04.22] - 2026-04-15

### Documentation

- **cmux-reviewer**: Add test-code finding policy for iter 2+([c583092](https://github.com/sussdorff/claude-code-plugins/commit/c58309255369c90b244038fd1a368999ac10fb04))

### Miscellaneous

- Update changelog([e7f4206](https://github.com/sussdorff/claude-code-plugins/commit/e7f4206cf5dbfee83f4ea11868b34f1a2f84aaf7))
## [2026.04.21] - 2026-04-14

### Bug Fixes

- **CCP-8t0**: Add mcp__open-brain__* tools to agent allowlists([5f7e92b](https://github.com/sussdorff/claude-code-plugins/commit/5f7e92b9aee360a9b8a14a263328596d1e7443b5))

### Miscellaneous

- Update changelog([70fedcd](https://github.com/sussdorff/claude-code-plugins/commit/70fedcdf0be833e8513a036dc8cdf19ce4b15d5d))
## [2026.04.20] - 2026-04-14

### Bug Fixes

- **session-close**: Add MCP tool names to agent tools: allowlist([b717795](https://github.com/sussdorff/claude-code-plugins/commit/b717795aebcb3dd65adecf1ad94f36a0026d3e34))

### Documentation

- **mira-aidbox**: Document /fhir-only rule and aidbox-format NPE bug([94aeb4a](https://github.com/sussdorff/claude-code-plugins/commit/94aeb4ac59a8339d4e17c435963c1945b037619b))

### Miscellaneous

- Update changelog([60d4aec](https://github.com/sussdorff/claude-code-plugins/commit/60d4aeceb68146119f4709225143e8aafd3a81c8))
## [2026.04.19] - 2026-04-14

### Documentation

- Add 2026-04-14 architecture session documents([c7569b5](https://github.com/sussdorff/claude-code-plugins/commit/c7569b54352e06bd10ba9bbee60f1d20b8687102))

### Miscellaneous

- Update changelog([212e990](https://github.com/sussdorff/claude-code-plugins/commit/212e990d8d3ad2b864a425712f6120a2033bc3a7))
## [2026.04.18] - 2026-04-14

### Documentation

- **home-infra**: Document LXC 119 kaji GitHub Actions runner([bce6565](https://github.com/sussdorff/claude-code-plugins/commit/bce6565fb95d0268e29600d70ef8b777cc0d5fae))
## [2026.04.17] - 2026-04-13

### Bug Fixes

- **session-close**: Create version tag after bump commit, not before([5ecdb00](https://github.com/sussdorff/claude-code-plugins/commit/5ecdb004d8cea27b7b5839300fddb66f9e88f7b6))
## [2026.04.16] - 2026-04-13

### Features

- **beads-workflow**: Add smart bead creation skill with type coaching and feature scenario gate([7c20f28](https://github.com/sussdorff/claude-code-plugins/commit/7c20f2864e540d55ee393c7136a06e83c113d7a7))
## [2026.04.15] - 2026-04-13

### Bug Fixes

- **bead-orchestrator**: Enforce hard stop on REROUTE_QUICK_FIX with no escape hatch([2293d4c](https://github.com/sussdorff/claude-code-plugins/commit/2293d4c2f8d0dc31879cc067f9adca5dc5fd7535))
## [2026.04.14] - 2026-04-13

### Features

- **bead-orchestrator**: Add effort estimation and quick-fix reroute in Phase 0([e79fc74](https://github.com/sussdorff/claude-code-plugins/commit/e79fc742887afeae5742f1f3ce3c4ec5b0052ca1))

### Miscellaneous

- Update changelog([32e65fe](https://github.com/sussdorff/claude-code-plugins/commit/32e65fe5a3882b98388e64b8c07e78f7b7c806ef))

### Refactoring

- **bead-workflow**: Establish opus/sonnet/codex tier architecture([c9087f5](https://github.com/sussdorff/claude-code-plugins/commit/c9087f5f60ff2e9f1c95a8915aa8f332e78f15bd))
## [2026.04.13] - 2026-04-12

### Features

- **wave-orchestrator**: Add effort estimation for unset beads in Phase 1([bd03426](https://github.com/sussdorff/claude-code-plugins/commit/bd0342670166b349caee112aa7dd9eed20473b87))

### Miscellaneous

- Update changelog([b930385](https://github.com/sussdorff/claude-code-plugins/commit/b9303856553a7e8b2213b511e8816dc5e8c969f4))
## [2026.04.12] - 2026-04-12

### Features

- **beads-workflow**: Add quick-fix agent for lightweight XS/S bead orchestration([edc85f3](https://github.com/sussdorff/claude-code-plugins/commit/edc85f37892c6d3be5dce1f2654b765590918022))

### Miscellaneous

- Update changelog([361d484](https://github.com/sussdorff/claude-code-plugins/commit/361d484e5bb8d42f11ff69ee0c09a6a82312525f))
## [2026.04.11] - 2026-04-12

### Bug Fixes

- **cmux**: Replace literal \n with send-key enter pattern across all agents([2729122](https://github.com/sussdorff/claude-code-plugins/commit/2729122820c165809110aaeae3935d233f3dd1dc))

### Miscellaneous

- Update changelog([8ed0c62](https://github.com/sussdorff/claude-code-plugins/commit/8ed0c622fb12cc7e515f168c731af8aaaaf4303e))
## [2026.04.10] - 2026-04-12

### Features

- **wave-orchestrator**: Add Phase 1.5b architecture review gate (CCP-b96)([00471ab](https://github.com/sussdorff/claude-code-plugins/commit/00471abdd2015f29bf0b0700f6eb88362bae3efb))
- **plugins**: Add version field to all plugin.json and extend version.sh for multi-plugin sync([2162fe3](https://github.com/sussdorff/claude-code-plugins/commit/2162fe388535ffb00e39726ef509433e37f8ce5b))
## [2026.04.9] - 2026-04-12

### Features

- **beads-workflow**: Add test quality gates, scope analysis, and learnings report([48c0fe2](https://github.com/sussdorff/claude-code-plugins/commit/48c0fe2649494083fec1c2da43aa67981f07350c))
- **beads-workflow**: Implement multi-model orchestration strategy (CCP-80r)([3888e06](https://github.com/sussdorff/claude-code-plugins/commit/3888e065fcd345d27bf6cc58e474efb3e79c4e3b))

### Miscellaneous

- Update changelog([6ac4ffe](https://github.com/sussdorff/claude-code-plugins/commit/6ac4ffef9317aa6f5b4eb77d619488ec0123841c))
## [2026.04.8] - 2026-04-12

### Bug Fixes

- **cmux-reviewer**: Drop hard 30-line fix-prompt cap([900de33](https://github.com/sussdorff/claude-code-plugins/commit/900de33cbdda86dd526dfad3447cab73e31ce0b4))
- **cmux-reviewer**: Use single-call send+newline with retry to fix race condition([a19cc12](https://github.com/sussdorff/claude-code-plugins/commit/a19cc12762d75dd4cd52534a9b33538e67b5b435))

### Documentation

- **cmux-reviewer**: Strip historical rationale from LEARN bullet([a0a611d](https://github.com/sussdorff/claude-code-plugins/commit/a0a611d1c36d9004777a5e1f0a7ba9c8edc8571f))

### Miscellaneous

- Update changelog([524d76e](https://github.com/sussdorff/claude-code-plugins/commit/524d76ec0d346acf9a7b8556e33b79690f8c3ae4))
## [2026.04.7] - 2026-04-11

### Bug Fixes

- **beads-workflow**: Route cmux-reviewer through codex-companion runtime([8827b8a](https://github.com/sussdorff/claude-code-plugins/commit/8827b8a7888e69d5922c3f39f70e0c0c876f30ef))

### Miscellaneous

- Update changelog([2aa36e0](https://github.com/sussdorff/claude-code-plugins/commit/2aa36e0ffa20054ca2515ffd533937571a7151cc))
## [2026.04.6] - 2026-04-11

### Bug Fixes

- **beads-workflow**: Bundle orchestrator library into plugin([e8c4d50](https://github.com/sussdorff/claude-code-plugins/commit/e8c4d509ae53a43d0de1b8873f9decd562efbab0))

### Miscellaneous

- Update changelog([30551f5](https://github.com/sussdorff/claude-code-plugins/commit/30551f53b30998568c3b1c11d029e56168973cf9))
## [2026.04.5] - 2026-04-11

### Documentation

- **beads-workflow**: Add three-stage escalation ladder to cmux-reviewer([48e1ee9](https://github.com/sussdorff/claude-code-plugins/commit/48e1ee9ca37e34713684198b71923c1f6570c4f3))
## [2026.04.4] - 2026-04-11

### Bug Fixes

- **beads-workflow**: Use fully qualified plugin namespace for subagent_type references([d8628e3](https://github.com/sussdorff/claude-code-plugins/commit/d8628e36e5cfd09de03042ab3693bfc5217c80d8))

### Miscellaneous

- Update changelog([29fd820](https://github.com/sussdorff/claude-code-plugins/commit/29fd820c20826d0af62934e6eecf0b5f61abec39))
## [2026.04.3] - 2026-04-11

### Features

- **session-close**: Sync plugin.json version when bumping VERSION file([f355915](https://github.com/sussdorff/claude-code-plugins/commit/f355915f86de0f677247217accf0ff3e65849432))

### Miscellaneous

- **plugins**: Remove version field from plugin.json and VERSION file([e4d9df5](https://github.com/sussdorff/claude-code-plugins/commit/e4d9df574576b764eb3e2f188d9fe7f97d50df2c))
## [2026.04.2] - 2026-04-11

### Features

- **hooks**: Migrate hooks to plugin namespaces and update cmux-reviewer([967e08e](https://github.com/sussdorff/claude-code-plugins/commit/967e08ef8592a78e2ab7e9082f4a4aba13079bb0))
## [2026.04.1] - 2026-04-11

### Bug Fixes

- **session-close**: Migrate handler scripts and update path reference([16e467e](https://github.com/sussdorff/claude-code-plugins/commit/16e467e092f5cfc6c3d1e888be249c7c5a787245))
- **session-close**: Update HANDLERS_DIR path to plugin cache location([3c2d903](https://github.com/sussdorff/claude-code-plugins/commit/3c2d903f50029d1ecb40e4388002a0d843faad6b))

### Features

- **agents**: Migrate all agents from malte/agents to plugin namespaces([e2eeb83](https://github.com/sussdorff/claude-code-plugins/commit/e2eeb83fc0e4e748d4cb7f308ce22416fe3d8241))
## [2026.04.0] - 2026-04-11

### Bug Fixes

- Ignore .claude symlink in addition to directory([8d0a9c7](https://github.com/sussdorff/claude-code-plugins/commit/8d0a9c737ac4af26cbb4715bb5e8ab027dad9f2b))
- Remove invalid 'category' field from all plugin.json files([87268bd](https://github.com/sussdorff/claude-code-plugins/commit/87268bdaf11fe3f6e3d2567b14276fa4bf2aea92))

### Documentation

- Document plugin skills discovery bug and workarounds([5732d12](https://github.com/sussdorff/claude-code-plugins/commit/5732d12b25baa9fa0037958e5d6ca29ae4928381))
- **sync-cache**: Clarify manual vs automated plugin cache sync([21b2eac](https://github.com/sussdorff/claude-code-plugins/commit/21b2eac48a1846116694852226c79e27b3360b8c))

### Features

- Add reference-file-compactor skill([00ca8d1](https://github.com/sussdorff/claude-code-plugins/commit/00ca8d12a9ac43f24f3ad79ae3142fd21af9c78d))
- Add plugin-tester for local plugin development workflow([4a49964](https://github.com/sussdorff/claude-code-plugins/commit/4a4996432bd1fd3820538b8e4d50c0716eeca796))
- Add plugin-developer plugin with marketplace-manager skill([91d7307](https://github.com/sussdorff/claude-code-plugins/commit/91d73076e381868434dedd2f8a26b01154a7601c))
- Add hook-creator skill for plugin-developer([d7d1a1c](https://github.com/sussdorff/claude-code-plugins/commit/d7d1a1c021bd3b8fe27fbdc9aed764ad4464e8d7))
- Add slash-command-creator skill to plugin-developer([c5b8372](https://github.com/sussdorff/claude-code-plugins/commit/c5b8372b6351dafd489caa981b9fa7158d258eb1))
- Add agent-creator skill for plugin-developer([18f1c02](https://github.com/sussdorff/claude-code-plugins/commit/18f1c02da186968713366ec75f6dc1f2e5e793fa))
- Add reference files and automation scripts to command-creator([25eba1e](https://github.com/sussdorff/claude-code-plugins/commit/25eba1e2972dd1c591b298a79b76cbab1b04ef5f))
- Add timing-matcher skill for Timing app export processing([392dbe8](https://github.com/sussdorff/claude-code-plugins/commit/392dbe85806d57c07be58954c6f946cb7589638a))
- Add playwright-mcp plugin for browser automation([ed061ee](https://github.com/sussdorff/claude-code-plugins/commit/ed061ee1cdfcd7f9b85ad3cbafc9f9c5717eb66a))
- Configure repository as official Claude Code marketplace([8f2a10b](https://github.com/sussdorff/claude-code-plugins/commit/8f2a10bf2443809bcceb10f07ba62bd7c5f11bcf))
- Add /install-plugin command to plugin-developer([07dee63](https://github.com/sussdorff/claude-code-plugins/commit/07dee637060a73f1271ed7716c124cb9faafef5c))
- Update /install-plugin to handle complete plugin unpacking([dffe5b5](https://github.com/sussdorff/claude-code-plugins/commit/dffe5b5fad0c513963e9ccf1941f13901528ffc1))
- Add prompt-library-tools plugin for Obsidian prompt extraction([a25f2d4](https://github.com/sussdorff/claude-code-plugins/commit/a25f2d48d94060550aa230614cf3fba79f342e1c))
- Add skill-forge plugin for skill quality scoring, auditing, and refactoring([02945a5](https://github.com/sussdorff/claude-code-plugins/commit/02945a57a141cc1424233097846ec18e79f40626))
- Restructure marketplace into 8 thematic plugin bundles([2d74892](https://github.com/sussdorff/claude-code-plugins/commit/2d748923e3b09cd483516644b52da12b45bfadd9))
- **dev-tools**: Add prd-generator, pester-test-engineer, feedback-extractor, spellcheck agents([f8983bd](https://github.com/sussdorff/claude-code-plugins/commit/f8983bdf2e3d5bdc066273f6401a778e6c4645e5))
- **beads**: Set up CCP issue tracking and improve dolt new-project docs([3430f98](https://github.com/sussdorff/claude-code-plugins/commit/3430f9826a62a4bdddec9d3fe97467dd5e20a051))

### Miscellaneous

- Remove duplicate .claude/ entry from gitignore([c01d317](https://github.com/sussdorff/claude-code-plugins/commit/c01d3179021aa20d39b6c7e78eff9ded87890ef7))
- Add sync-cache.sh script for manual plugin cache sync([e04a4de](https://github.com/sussdorff/claude-code-plugins/commit/e04a4deb39a65b30292bce762c2c22d40c5469a5))

### Refactoring

- Restructure reference-file-compactor as Claude Code plugin([57a83c0](https://github.com/sussdorff/claude-code-plugins/commit/57a83c06cfc1f1e7cd57de5da761aad734ae99cc))
- Replace bash script with Python for plugin installation([91ff653](https://github.com/sussdorff/claude-code-plugins/commit/91ff65329ebee73cebee12d31c9345f774e2ba28))
- Migrate bash/zsh scripts to Python for better portability([71c8d0b](https://github.com/sussdorff/claude-code-plugins/commit/71c8d0b462d949ab0d83a0a62577efd2730bae2a))
- Adopt pragmatic Python dependency approach([63997b8](https://github.com/sussdorff/claude-code-plugins/commit/63997b806adde76f32248b5caf612646daff96e7))
- Rename slash-command-creator to command-creator([bd1be5a](https://github.com/sussdorff/claude-code-plugins/commit/bd1be5a3f88568d805a0ae525a997340b5bab55a))
- Streamline command-creator skill (28% reduction)([eb24f60](https://github.com/sussdorff/claude-code-plugins/commit/eb24f602913b25725251566330108d76a591061c))
- Convert standalone skills to proper plugin structure([3401ffa](https://github.com/sussdorff/claude-code-plugins/commit/3401ffa2e1782c2314f82532a2d0428bbc468717))
- **command-creator**: Use model family names instead of version numbers([63f686c](https://github.com/sussdorff/claude-code-plugins/commit/63f686c1192e4afd96d7faa7e726e4afa4cff056))

