# Uber Data Platform — Roadmap (Rides Only) — نسخة معدّلة

> **تعديل مهم على الخطة:** قررنا نركّز دلوقتي على **موديول الـ Rides بس** (Ingestion + Geospatial Processing) بدل الأربع موديولز كاملين. يعني مفيش Drivers, Payments, Customer_Support دلوقتي — ده ممكن يترجع تاني بعدين كـ Phase مستقبلية لو حبينا نوسّع، بس مش جزء من النطاق الحالي.

كل مرحلة عليها حالة: ✅ خلصت / 🔄 شغالين عليها دلوقتي / ⏳ لسه.

---

## Phase 0 — Infrastructure (Docker) ✅ خلصت

- [x] `docker-compose.yml` بكل الـ services (Hadoop master/slave, Postgres, Hive Metastore, Trino, NiFi, Spark master/worker, Airflow, Superset)
- [x] كل ملفات الـ config اتعدلت لأسماء `uber-*`
- [x] `hive-metastore-entrypoint.sh` wrapper اتعمل ومظبوط جوه الـ compose
- [x] كل الـ images اتعملها build
- [x] `docker compose up -d` شغال، وكل الـ containers `Up` ومستقرة

---

## Phase 1 — HDFS Structure 🔄 شغالين عليها دلوقتي

بما إننا هنشتغل بس على Rides، مش لازم كل فولدرات bronze/silver/gold بتاعة drivers/payments/support — بس سيبهم موجودين مفيش مشكلة (هيبقوا فاضيين لحد ما نحتاجهم لاحقًا).

- [ ] تشغيل `scripts/setup_hdfs_dirs.sh` جوه `uber-hadoop-master`
- [ ] التأكد من `hdfs dfs -ls -R /data` إن على الأقل دول موجودين:
  ```
  /data/bronze/rides
  /data/silver/staging_rides_geo
  /data/gold/fact_rides   (أو أي اسم هنتفق عليه للـ Gold layer بتاع الـ Rides)
  /data/quarantine/rides
  ```
- [ ] التأكد من الـ DataNodes الاتنين `Live` عبر `hdfs dfsadmin -report`

---

## Phase 2 — Rides Data Acquisition ⏳

- [ ] تحميل NYC TLC Trip Data (أو أي مصدر عام تاني فيه lat/lon حقيقي) كمصدر الـ backbone
- [ ] تحويل الأعمدة لتطابق الـ schema بتاعنا:
  `trip_id, start_lat, start_lon, end_lat, end_lon, start_time, end_time, distance`
  (ملحوظة: `driver_id` هنشيله من الـ schema دلوقتي طالما مفيش موديول Drivers — هنرجعه لو ضفنا الموديول ده تاني)
- [ ] تحديد حجم البيانات (Dev Mode: عينة صغيرة أول حاجة، بعدين نكبّر لو الكل شغال تمام)
- [ ] حط البيانات في `data/raw/rides/`

---

## Phase 3 — Ingestion إلى Bronze ⏳

بما إن المصدر دلوقتي واحد بس (Rides)، مش لازم NiFi معقد — أبسط حل:

- [ ] سكريبت بسيط (Python/Spark) بيحوّل الملفات الخام (CSV/Parquet) لـ Parquet ويكتبها في:
  `/data/bronze/rides/year=YYYY/month=MM/day=DD/`
- [ ] (اختياري لاحقًا) لو حبينا نبني flow NiFi بدل السكريبت المباشر — نأجله لحد ما نحتاج نضيف مصادر تانية فعلاً

---

## Phase 4 — Bronze → Silver (Rides Geospatial Processing) ✅ الكود جاهز / 🔄 محتاج اختبار

الكود ده اتكتب فعلاً ومش محتاج تعديل كبير — بس هنشيل منه أي إشارة لـ `driver_id` لحد ما نرجع للموديول ده:

- [x] `common/schemas.py` → `RIDES_SILVER_SCHEMA` (هنعدلها نشيل `driver_id` مؤقتًا)
- [x] `common/cleaning.py` → `standardize_rides`, `handle_nulls_rides`, `split_invalid_rides`
- [x] `common/geo.py` → H3 geo-hashing + trip_duration_sec
- [x] `common/dedup.py` → dedup على `trip_id`
- [x] `batch/bronze_to_silver_rides.py`
- [ ] تشغيله فعليًا بعد ما تكون بيانات Bronze موجودة (Phase 3)
- [ ] مراجعة نسبة الـ quarantine

---

## Phase 5 — Silver → Gold (Rides Aggregates) ⏳ محتاج إعادة كتابة بسيطة

بما إننا مش هنعمل `Fact_Trip` الموحّد (كان محتاج Payments/Support/Drivers)، الـ Gold layer دلوقتي هيبقى مباشرة مبني على `Staging_Rides_Geo` نفسها + شوية جداول مجمّعة:

- [ ] `fact_rides` (نسخة Gold من staging_rides_geo، partitioned)
- [ ] `agg_trips_daily` (عدد الرحلات + متوسط المدة/المسافة لكل يوم)
- [ ] `agg_trips_by_geohash` (عدد الرحلات لكل منطقة — start_geo_hash)
- [ ] `agg_trips_by_hour` (توزيع الرحلات على مدار اليوم)
- [ ] تعديل `common/aggregations.py` و`batch/silver_to_gold.py` عشان يشيلوا كل حاجة متعلقة بـ payments/support/driver_kpi

---

## Phase 6 — Hive / Trino Tables ⏳ محتاج إعادة كتابة بسيطة

- [ ] تعديل `sql/hive_ddl/gold_tables.sql` عشان يسجل بس: `fact_rides`, `agg_trips_daily`, `agg_trips_by_geohash`, `agg_trips_by_hour`
- [ ] شيل تعريفات `fact_trip`, `agg_revenue_*`, `agg_cancellation_*`, `agg_driver_kpis` مؤقتًا (أو سيبهم معلّقين بـ comment لحد ما نرجعلهم)
- [ ] تشغيل الملف عبر Trino والتأكد إن الجداول قابلة للاستعلام

---

## Phase 7 — KPIs & Superset Dashboard ⏳

KPIs بتاعة Rides بس دلوقتي:
- [ ] Total Trips / Trips per day
- [ ] Average Trip Duration & Distance
- [ ] Trips by Geo-hash (أكتر المناطق طلبًا)
- [ ] Trips by Hour of Day / Day of Week
- [ ] Dashboard بسيط في Superset يجمعهم

---

## Phase 8 — Orchestration (Airflow) ⏳

DAG أبسط بكتير من الأصلي:
```
ingest_rides → process_rides (bronze_to_silver_rides.py) → build_gold (silver_to_gold.py) → refresh_trino_partitions
```

---

## Phase 9 — Testing ⏳

- [ ] Unit tests لـ `common/geo.py` (H3 correctness)
- [ ] Data Quality tests لـ `split_invalid_rides`
- [ ] End-to-End test على عينة صغيرة

---

## Phase 10 — Documentation ⏳

- [ ] README محدّث يوضح إن النطاق الحالي Rides-only
- [ ] Data dictionary لـ `staging_rides_geo` + جداول الـ Gold
- [ ] توثيق إن Drivers/Payments/Support اتأجلوا (مش اتلغوا) لمرحلة لاحقة

---

## حاجات من الخطة القديمة بقت "مؤجلة" مش محذوفة (لو حبينا نرجعلها بعدين)

الملفات دي اتكتبت فعلاً وهتفضل موجودة في الريبو، بس مش هنستخدمها دلوقتي:
`common/window_metrics.py`, `common/cancellation_rules.py`, وأجزاء من `common/schemas.py` و`common/cleaning.py` و`common/aggregations.py` الخاصة بـ Drivers/Payments/Support، وكل ملفات `batch/bronze_to_silver_drivers.py`, `bronze_to_silver_driver_events.py`, `bronze_to_silver_payments.py`, `bronze_to_silver_support.py`.

---

## إيه اللي هنعمله دلوقتي بالظبط (Next Immediate Steps)

1. نخلص Phase 1 (تشغيل `setup_hdfs_dirs.sh` والتأكد من الـ HDFS structure)
2. نبدأ Phase 2 (تحميل بيانات Rides الحقيقية)
3. نعدّل `common/schemas.py` نشيل `driver_id` من `RIDES_SILVER_SCHEMA` مؤقتًا
