# Publish v0.5.0 to GitHub

Use the clean GitHub working folder you created earlier:

```powershell
cd C:\docker\thing-planner-workos-git
```

Copy the new release into the repo:

```powershell
robocopy `
  "C:\docker\thing-planner-workos-v0.5.0\thing-planner-workos-v0.5.0" `
  "C:\docker\thing-planner-workos-git" `
  /MIR `
  /XD .git .venv __pycache__ `
  /XF *.pyc
```

Commit and push:

```powershell
git status
git add .
git commit -m "Release Thing Planner WorkOS v0.5.0"
git push origin main
```

Create/update release tag:

```powershell
git tag -f v0.5.0
git push origin v0.5.0 --force
```

Verify:

```powershell
git status
git log --oneline --max-count=5
```
