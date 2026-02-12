.PHONY: up down logs geo-pipeline geo-fetch route-demo route-cpp gpx-demo geo-demo postgis-load web-demo-assets

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f --tail=100

geo-pipeline:
	python3 services/geo-pipeline/run_pipeline.py

geo-fetch:
	python3 services/geo-pipeline/fetch_overpass.py --bbox "48.8156,2.2241,48.9022,2.4699"

route-demo:
	python3 services/geo-pipeline/build_global_route.py

route-cpp:
	python3 services/geo-pipeline/solve_cpp_route.py

gpx-demo:
	python3 services/geo-pipeline/segment_to_gpx.py --target-count 10

geo-demo: geo-pipeline route-cpp gpx-demo

postgis-load:
	python3 services/geo-pipeline/load_to_postgis.py

web-demo-assets:
	bash scripts/sync_demo_assets.sh
