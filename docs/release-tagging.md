# 自动打标机制 / Release tagging mechanism

本文件是「发版后打版本标签」的仓内正本（Refs #31）。`docs/RELEASING.md` 的「自动打标签机制」一节是摘要，
与本文冲突时以本文为准。

## 触发

**发版 PR 合入 `main`。** 发版 PR 指同一个 PR 内完成两件事：`SKILL.md` 的 `metadata.version` 改为新版本，
且 `CHANGELOG.md` 把 `[Unreleased]` 移入对应的 `## [X.Y.Z]` 小节（见 `docs/RELEASING.md`「发版」第 1 步）。
未改版本号的合并不触发打标。若 `v<版本>` 标签已存在，不重复打、不覆盖。

## 命名

`v<semver>`，例如 `v1.1.0`。版本号取自被封版的 `SKILL.md` `metadata.version`，
并须与 `CHANGELOG.md` 小节一致。标签为附注标签（`git tag -a`），打在发版 PR 的**合并提交**上。

## 执行身份与步骤

- **当前（已生效）**：人工/中枢身份——有推送标签权限的合并方（Jarvis，即合并所有者）。
  外部 Claude 会话不打标（推送标签会创建公开 Release，需要权限批准；见 #30）。
- **目标（#31 提案，尚未落地）**：新增 `.github/workflows/tag-release.yml`，由 `github-actions[bot]`
  以 `GITHUB_TOKEN` 执行，仅授予对应 job 所需权限。本文件不声称该工作流已存在；落地时由该 PR 更新本节。

步骤（无论哪种身份，动作一致）：

1. 确认发版 PR 已合入 `main`，并取得其合并提交 SHA。
2. 确认该提交上 `SKILL.md` 版本与 `CHANGELOG.md` 小节一致，且 `v<版本>` 尚不存在。
3. 在合并提交上打附注标签并推送：

   ```bash
   git fetch origin main
   git tag -a vX.Y.Z -m "vX.Y.Z" <合并提交SHA>
   git push origin vX.Y.Z
   ```

4. 标签推送后由 `.github/workflows/release.yml` 接手：核对门禁、产出附件并签名、创建 GitHub Release
   （详见 `docs/RELEASING.md`）。

## 回滚

标签打错（打在错误提交、版本号不符）时：

1. **删除误打的 tag**（本地与远端：`git tag -d vX.Y.Z && git push origin :refs/tags/vX.Y.Z`）。
2. **revert** 发版合并提交（新开 PR，不改写 `main` 历史）。
3. 修正后用新的提交重新发版。

**严禁对 tag 改指（re-point）**：不得 `git tag -f` 或强推把已有标签指向别的提交。
已被消费（已有 GitHub Release、已被签名/证明引用）的版本，让调用者改用上一个标签，修复走新的补丁版本。

## 首例

`v1.1.0` 由人工打在 `0c8e6dab`（PR #28/#29 合入后的 `main` 提交；#29 的合并提交为 `0c8e6dab6bd9…`），
是本机制的**手工第一实例**，也是后续自动化要复现的行为基线。

*English summary:* the trigger is a release PR merging to `main`; the tag is `v<semver>` (e.g. `v1.1.0`), an annotated tag on the merge commit.
Today it is cut by the maintainer/Jarvis; the `tag-release.yml` automation proposed in #31 is not yet in the repo.
Rollback = delete the mistaken tag and revert the release merge; never re-point a tag.
First instance: `v1.1.0` cut by hand at `0c8e6dab` after #28/#29 merged.
