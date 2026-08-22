from intelio.services.github import get_commit_details


def build_code_evidence(username, repository_name, commits):
    """
    Build lightweight code evidence from recent commits.

    Only the latest five commits are inspected.
    """

    evidence = []

    for commit in commits[:5]:
        details = get_commit_details(
            username,
            repository_name,
            commit["sha"]
        )

        changed_files = []

        for file in details["files"]:
            changed_files.append({
                "filename": file["filename"],
                "status": file["status"],
                "additions": file["additions"],
                "deletions": file["deletions"],
                "patch": file["patch"],
            })

        evidence.append({
            "sha": details["sha"],
            "message": details["message"],
            "repository": details["repository"],
            "files": changed_files,
        })

    return evidence