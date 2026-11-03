# 发版、校验与回滚 / Releasing, verifying and rolling back

## 发版 / Cut a release

1. 在一个 PR 里把 `CHANGELOG.md` 的 `[Unreleased]` 条目移到新的 `## [X.Y.Z] - YYYY-MM-DD` 小节，
   并把 `SKILL.md` frontmatter 的 `metadata.version` 改成 `X.Y.Z`。合并该 PR。
2. 在合并后的 `main` 上打标签并推送：

   ```bash
   git fetch origin main && git tag -a vX.Y.Z -m "vX.Y.Z" origin/main && git push origin vX.Y.Z
   ```

3. `.github/workflows/release.yml` 会自动：核对标签所在提交在 `main` 上、标签与 `SKILL.md` 版本一致、CHANGELOG 有对应小节；
   跑与 PR CI 相同的门禁（ruff、单元测试、`validate_skill.py`、`demo/eval.sh`、样例可复现）；
   生成源码包、可复现的 CycloneDX SBOM 与 `SHA256SUMS`；对每个文件做 Sigstore 无密钥签名
   （`<文件>.sigstore.json`）；生成 GitHub 构建来源证明（SLSA v1）；最后创建 GitHub Release。
   任一步失败都不会发布。所有 action 按提交 SHA 固定。

## 自动打标签机制 / Auto-tag mechanism（#31 裁定采纳）

第 2 步的打标签动作由此机制泛化为自动执行；规则如下：

1. **触发**：发版 PR 合并进 `main` 时，在该合并提交上打标签（附注标签，随后由第 3 步的 `release.yml` 接手）。
2. **命名**：`v<semver>`，取自被封版的版本号（即该 PR 中 `SKILL.md` `metadata.version`，且须与 `CHANGELOG.md` 小节一致）。
3. **回滚**：删除该标签并回退（revert）发版合并提交；**绝不把已有标签改指到别的提交**。修正后用新的提交重新发版；
   若该版本已对外发布（已有 GitHub Release），仍按下文「回滚」一节让调用者改用上一个标签，修复走新的补丁版本。

**先例**：`v1.1.0` 由人工打在合并提交 `0c8e6dab`（issue #30），是本机制泛化的首例。

*English summary:* when a release PR merges to `main`, a tag `v<semver>` (the version being sealed) is cut on the merge commit.
Rollback = delete the tag and revert the release merge; never re-point an existing tag. Precedent: `v1.1.0` on `0c8e6dab` (#30), cut manually.

## 校验 / Verify a release

```bash
sha256sum -c SHA256SUMS
# 签名：确认文件由本仓库 release.yml 在该标签上签出
cosign verify-blob founder-visual-director-X.Y.Z.tar.gz \
  --bundle founder-visual-director-X.Y.Z.tar.gz.sigstore.json \
  --certificate-identity "https://github.com/HUIIIM/founder-visual-director/.github/workflows/release.yml@refs/tags/vX.Y.Z" \
  --certificate-oidc-issuer https://token.actions.githubusercontent.com
# 来源证明：确认构建来自本仓库的 GitHub Actions
gh attestation verify founder-visual-director-X.Y.Z.tar.gz --repo HUIIIM/founder-visual-director
```

SBOM 可复现：在标签上设 `SOURCE_DATE_EPOCH=$(git log -1 --format=%ct vX.Y.Z)` 后运行
`python3 scripts/make_sbom.py X.Y.Z out.json`，结果应与发布页的 `.cdx.json` 逐字节一致。

## 回滚 / Roll back

本仓库没有部署环境：调用者加载的是某个标签下的 `SKILL.md` 与 `references/`。回滚 = 让调用者改用上一个标签：

```bash
git -C <skill 目录> fetch --tags && git -C <skill 目录> checkout vPREVIOUS
```

不要删除或改写已发布的标签；修复走新的补丁版本（X.Y.Z+1）。
