# Publish v0.2.0 to GitHub

Recommended repository:

```text
https://github.com/echofoxx/thing-planner-workos
```

## New repository

```powershell
cd C:\docker\thing-planner-workos-v0.2.0\thing-planner-workos-v0.2.0

git init
git branch -M main
git add .
git commit -m "Initial commit: Thing Planner WorkOS v0.2.0"

gh repo create echofoxx/thing-planner-workos --public --source . --remote origin --push

git tag v0.2.0
git push origin v0.2.0
```

## Existing repository

```powershell
cd C:\docker\thing-planner-workos
# replace the files with this release content, then:

git status
git add .
git commit -m "Release v0.2.0 data layer foundation"
git push origin main

git tag v0.2.0
git push origin v0.2.0
```
