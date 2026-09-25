def add_task(tasks, task):
    """Add a task to the task list."""
    tasks.append(task)
    return tasks


def complete_task(tasks, task):
    """Mark a task as completed."""
    if task in tasks:
        tasks.remove(task)
        return True

    return False


def main():
    tasks = []

    add_task(tasks, "Finish assignment")
    add_task(tasks, "Prepare presentation")

    print("Tasks:", tasks)


if __name__ == "__main__":
    main()