# Publish v0.6.0 to GitHub

Use your clean repo folder:

```powershell
cd C:\docker\thing-planner-workos-git
```

Copy the v0.6.0 files into the repo:

```powershell
robocopy `
  "C:\docker\thing-planner-workos-v0.6.0\thing-planner-workos-v0.6.0" `
  "C:\docker\thing-planner-workos-git" `
  /MIR `
  /XD .git .venv __pycache__ `
  /XF *.pyc
```

Commit and push:

```powershell
git status
git add .
git commit -m "Release Thing Planner WorkOS v0.6.0"
git push origin main

git tag -f v0.6.0
git push origin v0.6.0 --force
```
