# AONE 流水线

## push-to-github.yaml

将当前仓库 **master** 分支同步到 GitHub 目标仓库的 **main** 分支（可改参数）。

### 使用步骤

1. 在 AONE 中创建流水线，选择「由代码库创建」，关联本仓库。
2. 流水线定义选择：`.aone/push-to-github.yaml`。
3. **触发方式**：在流水线或 Job 设置中选择 **手动触发**（不配置定时或代码 push 触发即可）。
4. 配置 CI/CD 变量与密钥（Settings → CI/CD → Variables）：
   - **Secret**：`agbaccount_github_token`（GitHub Token，需 repo 权限）
   - **Variable**：`agbaccount_github_username`（GitHub 用户名）
   - **Variable**：`agbaccount_github_email`（Git 提交用邮箱）
5. 需要同步时在 AONE 中点击「运行」执行流水线。

### 参数说明

| 参数 | 默认值 | 说明 |
|------|--------|------|
| github_repo | agentbay-ai/agentbay-skills | 目标 GitHub 仓库 (owner/repo) |
| source_branch | master | 要同步的源分支 |
| target_branch | main | GitHub 上的目标分支 |
| runs_on_resources | 2-8Gi | 运行资源规格 |

### 行为说明

- 使用 `checkout` 拉取 `source_branch`（默认 master）。
- 校验 GitHub Token、仓库格式及仓库访问权限。
- **排除 `.aone`**：在推送前从待推送内容中移除 `.aone` 目录（仅内部使用的 CI 配置，不推送到 GitHub）。
- 基于源分支创建临时分支 `sync-to-github`，在该分支上提交「排除 .aone」的变更后，推送到 GitHub 的 `target_branch`（默认 main）。
