This script can help you find and remove unused AWS snapshots and volumes.

There is hardcoded list of regions that it searches, adjust the value to suit your needs.

Use `snapshot.py snapshot-report` to generate `report.csv` containing information about all snapshots.

`snapshot.py snapshot-cleanup` lets you interactively delete snapshot if it finds it is referencing unexisting resources.

```
./snapshots.py --help
Usage: snapshots.py [OPTIONS] COMMAND [ARGS]...

  Helper commands for Snapshots management.

Options:
  --help  Show this message and exit.

Commands:
  snapshot-cleanup  Find and delete unreferenced snapshots.
  snapshot-delete   Delete single snapshot by id.
  snapshot-report   Find unreferenced snapshots.
  volume-cleanup    Find and delete unused volumes.
```