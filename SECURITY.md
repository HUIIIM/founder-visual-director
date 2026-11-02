# Security Policy / 安全策略

## Reporting a vulnerability / 报告漏洞

Please do not open a public issue for security problems (for example a committed secret, or a way to make the
demo mark a red-line input as passing). Use GitHub private vulnerability reporting on this repository
(Security → Report a vulnerability) if it is enabled, or contact the maintainer [@HUIIIM](https://github.com/HUIIIM).

请勿用公开 issue 报告安全问题（例如误提交的密钥，或能让 demo 把红线输入判为通过的方法）。请使用本仓库的
GitHub 私密漏洞报告（若已开启），或联系维护者 [@HUIIIM](https://github.com/HUIIIM)。

## Scope / 范围

This repository contains a skill definition, reference documents and a zero-dependency demo. It runs no service
and its files hold no user data. The skill does, however, direct the production of images of a real, identifiable
person (the founder): the likeness assets, the clone model (`model_id`) and its consent record live outside this
repository. A way to make the skill or its checkers approve a post that uses a revoked model asset or the standard
portrait is in scope. See [docs/PRIVACY.md](docs/PRIVACY.md) for data handling.

本仓库文件不含用户数据，但 skill 指导的是真实可识别人物（创始人）的肖像生产；肖像素材、克隆模型（`model_id`）
及其授权记录在仓库外。能让 skill 或校验脚本放行「已撤回授权的模特资产」或「白底标准照」的方法属于安全问题。

## Supported versions / 支持版本

Only the latest commit on `main` is supported.
