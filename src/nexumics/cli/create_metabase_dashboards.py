"""Create Nexumics dashboards in a local Metabase instance."""

from __future__ import annotations

import sys

from nexumics.metabase_dashboards import (
    MetabaseApiError,
    create_dashboards,
    dashboard_url,
    load_metabase_config_from_env,
)


def main() -> int:
    try:
        config = load_metabase_config_from_env()
        created = create_dashboards(**config)
    except MetabaseApiError as exc:
        print(f"Metabase dashboard creation failed: {exc}", file=sys.stderr)
        return 1

    print("Created Metabase dashboards:")
    for name, dashboard_id in created:
        print(f"- {name}: {dashboard_url(config['base_url'], dashboard_id, name)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
