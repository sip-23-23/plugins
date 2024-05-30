import json
import os
import subprocess


def configure_git():
    subprocess.run(
        ["git", "config", "--global", "user.email", '"lightningd@plugins.repo"']
    )
    subprocess.run(["git", "config", "--global", "user.name", '"lightningd"'])


# gather data
def collect_gather_data(results, success):
    gather_data = {}
    for t in results:
        p = t[0]
        from . import test

        if test.has_testfiles(p):
            if success or t[1]:
                gather_data[p.name] = "passed"
            else:
                gather_data[p.name] = "failed"
    return gather_data


def push_gather_data(results, success, workflow, python_version):
    print("Pushing gather data...")
    configure_git()
    subprocess.run(["git", "fetch"])
    subprocess.run(["git", "checkout", "badges"])

    data = collect_gather_data(results, success)

    any_changes = False
    for plugin_name, result in data.items():
        any_changes |= update_and_commit_gather_data(
            plugin_name, result, workflow, python_version
        )

    if any_changes:
        subprocess.run(["git", "push", "origin", "badges"])
    print("Done.")


def update_and_commit_gather_data(plugin_name, result, workflow, python_version):
    _dir = f"badges/gather_data/{workflow}/{plugin_name}"
    filename = os.path.join(_dir, f"python{python_version}.txt")
    os.makedirs(_dir, exist_ok=True)
    with open(filename, "w") as file:
        print(f"Writing {filename}")
        file.write(result)

    output = subprocess.check_output(["git", "add", "-v", filename]).decode("utf-8")  #
    if output != "":
        subprocess.run(
            [
                "git",
                "commit",
                "-m",
                f"Update {plugin_name} test result to '{result}' ({workflow} workflow)",
            ]
        )
        return True
    return False


# badges data
def collect_badges_data(results, success):
    badges_data = {}
    for t in results:
        p = t[0]
        from .test import has_testfiles

        if has_testfiles(p):
            if success or t[1]:
                badges_data[p.name] = True
            else:
                badges_data[p.name] = False
    return badges_data


def update_and_commit_badge(plugin_name, passed, workflow, python_version):
    json_data = {"schemaVersion": 1, "label": "", "message": " ✔ ", "color": "green"}
    if not passed:
        json_data.update({"message": "✗", "color": "red"})

    badges_dir = f"badges/gather_data/{workflow}/{python_version}"
    filename = os.path.join(
        badges_dir, f"{plugin_name}_{workflow}_python{python_version}.json"
    )
    os.makedirs(badges_dir, exist_ok=True)
    with open(filename, "w") as file:
        print(f"Writing {filename}")
        file.write(json.dumps(json_data))

    output = subprocess.check_output(["git", "add", "-v", filename]).decode("utf-8")  #
    print(f"output:{output}.")
    if output != "":
        subprocess.run(
            [
                "git",
                "commit",
                "-m",
                f'Update {plugin_name} badge to {"passed" if passed else "failed"} ({workflow})',
            ]
        )
        return True
    return False


def push_badges_data(data, workflow):
    print("Pushing badge data...")
    configure_git()
    subprocess.run(["git", "fetch"])
    subprocess.run(["git", "checkout", "badges"])

    any_changes = False
    for plugin_name, passed in data.items():
        any_changes |= update_and_commit_badge(plugin_name, passed, workflow)

    if any_changes:
        subprocess.run(["git", "push", "origin", "badges"])
    print("Done.")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Plugins completion script")
    parser.add_argument("data", nargs="*", default={}, help="Badges update data")
    parser.add_argument("workflow", type=str, help="Name of the GitHub workflow")
    args = parser.parse_args()

    push_badges_data(args.data, args.workflow)
