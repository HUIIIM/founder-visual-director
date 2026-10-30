# 发版、校验与回滚 / Releasing, verifying and rolling back

## 发版 / Cut a release

1. 在一个 PR 里把 `CHANGELOG.md` 的 `[Unreleased]` 条目移到新的 `## [X.Y.Z] - YYYY-MM-DD` 小节，
   并把 `SKILL.md` frontmatter 的 `metadata.version` 改成 `X.Y.Z`。合并该 PR。
2. 在合并后的 `main` 上打标签并推送：

   ```bash
   git fetch origin main && git tag -a vX.Y.Z -m "vX.Y.Z" origin/main && git push origin vX.Y.Z
   ```

3. `.github/workflows/release.yml` 会自动：核对标签与 `SKILL.md` 版本一致、CHANGELOG 有对应小节；
   跑单元测试与 `demo/eval.sh`；生成源码包、CycloneDX SBOM、`SHA256SUMS`；创建 GitHub Release；
   再由 SLSA 生成器附上签名的构建来源证明（`*.intoto.jsonl`）。任一步失败都不会发布。

## 校验 / Verify a release

```bash
sha256sum -c SHA256SUMS
slsa-verifier verify-artifact founder-visual-director-X.Y.Z.tar.gz \
  --provenance-path multiple.intoto.jsonl \
  --source-uri github.com/HUIIIM/founder-visual-director --source-tag vX.Y.Z
```

`slsa-verifier` 见 https://github.com/slsa-framework/slsa-verifier 。

## 回滚 / Roll back

本仓库没有部署环境：调用者加载的是某个标签下的 `SKILL.md` 与 `references/`。回滚 = 让调用者改用上一个标签：

```bash
git -C <skill 目录> fetch --tags && git -C <skill 目录> checkout vPREVIOUS
```

不要删除或改写已发布的标签；修复走新的补丁版本（X.Y.Z+1）。
