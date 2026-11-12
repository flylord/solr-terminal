import os
import sys

from solr_tui.app import SolrTuiApp, resolve_credentials


def main() -> None:
    SolrTuiApp(resolve_credentials(sys.argv[1:], os.environ)).run()


if __name__ == "__main__":
    main()
