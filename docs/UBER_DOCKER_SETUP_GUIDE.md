# Uber Data Platform — Docker Setup & Run Guide

هذا الملف يشرح بالترتيب طريقة تجهيز وتشغيل مشروع **Uber Data Platform** باستخدام Docker Desktop، من أول تحميل الملفات المطلوبة لحد تشغيل الـContainers.

> **مكان تنفيذ الأوامر:** افتح PowerShell داخل الـproject root:
>
> `D:\course\Projects\_Data\uber-data-platform`

---

## 1. المتطلبات قبل البدء

تأكد أن الآتي شغال:

- Docker Desktop
- Docker Engine
- PowerShell
- المشروع موجود على الجهاز

اختبر Docker:

```powershell
docker --version
docker compose version
```

المفروض يظهر لك Version لكل واحد.

اختبر أن Docker Desktop شغال:

```powershell
docker info
```

لو الأمر رجع معلومات Docker بدون Error، نقدر نكمل.

---

# 2. ادخل إلى Project Root

```powershell
cd D:\course\Projects\_Data\uber-data-platform
```

تأكد أنك في المكان الصحيح:

```powershell
Get-ChildItem
```

المفروض تشوف حاجات مثل:

```text
docker-compose.yml
airflow
batch
common
config
docker
nifi
scripts
sql
tests
```

---

# 3. التأكد من Hadoop file

الـHadoop Dockerfile في المشروع يحتاج ملف:

```text
docker/hadoop/hadoop-3.3.6.tar.gz
```

لو الملف غير موجود، لازم ننزله قبل Build.

Apache يوفر `hadoop-3.3.6.tar.gz` من أرشيف الإصدارات، وحجم الملف حوالي 696 MB.

الرابط الرسمي:

https://archive.apache.org/dist/hadoop/common/hadoop-3.3.6/

## تحميله باستخدام PowerShell

نفّذ:

```powershell
Invoke-WebRequest `
  -Uri "https://archive.apache.org/dist/hadoop/common/hadoop-3.3.6/hadoop-3.3.6.tar.gz" `
  -OutFile ".\docker\hadoop\hadoop-3.3.6.tar.gz"
```

بعد التحميل تأكد:

```powershell
Test-Path ".\docker\hadoop\hadoop-3.3.6.tar.gz"
```

لو ظهر:

```text
True
```

يبقى الملف موجود في المكان الصحيح.

يمكنك أيضًا التأكد من حجمه:

```powershell
Get-Item ".\docker\hadoop\hadoop-3.3.6.tar.gz" |
Select-Object Name, Length
```

> **ملاحظة:** الملف كبير، فلا تقلق إذا أخذ التحميل وقتًا.

---

# 4. Build الـHadoop Master أولًا

هذه أهم خطوة بسبب أن Hadoop Slave يعتمد على Hadoop Master image.

نفّذ:

```powershell
docker compose build uber-hadoop-master
```

الـImage الناتجة اسمها:

```text
uber-hadoop-base-master
```

بعد انتهاء الـBuild تأكد أنها موجودة:

```powershell
docker images | findstr uber-hadoop
```

المفروض تشوف:

```text
uber-hadoop-base-master
```

---

# 5. Build Hadoop Slaves

بعد نجاح Master فقط، ابنِ الـSlaves:

```powershell
docker compose build uber-hadoop-slave1
```

ثم:

```powershell
docker compose build uber-hadoop-slave2
```

الـSlave يستخدم:

```text
uber-hadoop-base-master
        ↓
Dockerfile.slave
        ↓
uber-hadoop-slave-image
```

لذلك لا تبدأ بالـSlave قبل نجاح الـMaster.

تأكد:

```powershell
docker images | findstr uber-hadoop
```

المفروض يكون عندك:

```text
uber-hadoop-base-master
uber-hadoop-slave-image
```

---

# 6. Build Jupyter

بعد Hadoop:

```powershell
docker compose build uber-jupyter
```

الـImage الناتجة:

```text
uber-jupyter-image
```

تأكد:

```powershell
docker images | findstr uber-jupyter
```

---

# 7. Build Airflow

في `docker-compose.yml` يوجد أكثر من Airflow service، لكنهم يستخدمون **نفس Dockerfile ونفس Image**:

```text
uber-airflow-init
uber-airflow-api-server
uber-airflow-scheduler
uber-airflow-dag-processor
```

لذلك لا تحتاج تعمل Build منفصل لكل واحد.

ابنِ الـImage مرة واحدة:

```powershell
docker compose build uber-airflow-init
```

والـImage الناتجة:

```text
uber-airflow-image
```

تأكد:

```powershell
docker images | findstr uber-airflow
```

---

# 8. Build Superset

يوجد Service للـSuperset وService للـSuperset initialization، لكن الاثنين يستخدمان نفس الـImage:

```text
uber-superset-init
uber-superset
```

ابنِ الـImage:

```powershell
docker compose build uber-superset-init
```

تأكد:

```powershell
docker images | findstr uber-superset
```

---

# 9. الخدمات التي لا تحتاج Build محلي

الخدمات التالية تستخدم Images جاهزة من Docker Registry، لذلك Docker سيقوم بتحميلها تلقائيًا عند الحاجة:

```text
PostgreSQL
Hive Metastore
Trino
NiFi
Spark Master
Spark Worker
```

ومن الـdocker-compose:

```text
postgres:13-alpine
apache/hive:3.1.3
trinodb/trino:latest
apache/nifi:1.25.0
bde2020/spark-master:3.3.0-hadoop3.3
bde2020/spark-worker:3.3.0-hadoop3.3
```

---

# 10. التأكد من كل الـImages

نفّذ:

```powershell
docker images
```

مهم أن تكون الـImages المحلية الخاصة بالمشروع موجودة:

```text
uber-hadoop-base-master
uber-hadoop-slave-image
uber-jupyter-image
uber-airflow-image
uber-superset-image
```

والـImages الجاهزة سيتم تحميلها من Docker Registry عند تشغيل المشروع إذا لم تكن موجودة.

---

# 11. تشغيل كل الـContainers

بعد نجاح كل الـBuilds:

```powershell
docker compose up -d
```

Docker Compose سيقوم بـ:

1. إنشاء Network
2. إنشاء Volumes
3. تحميل Images المطلوبة
4. إنشاء Containers
5. تشغيل الخدمات حسب dependencies الموجودة في `docker-compose.yml`

---

# 12. التأكد أن الـContainers شغالة

نفّذ:

```powershell
docker compose ps
```

أو:

```powershell
docker ps
```

المفروض تشوف Containers مثل:

```text
uber-hadoop-master
uber-hadoop-slave1
uber-hadoop-slave2
uber-postgres
uber-hive-metastore
uber-trino
uber-nifi
uber-spark-master
uber-spark-worker
uber-jupyter
uber-airflow-init
uber-airflow-api-server
uber-airflow-scheduler
uber-airflow-dag-processor
uber-superset-init
uber-superset
```

---

# 13. مهم: uber-airflow-init و uber-superset-init

وجود:

```text
uber-airflow-init
uber-superset-init
```

بحالة:

```text
Exited (0)
```

ليس بالضرورة Error.

هذه Containers وظيفتها initialization فقط.

مثلاً Airflow Init يعمل:

```text
airflow db migrate
+
create admin user
```

وبعد انتهاء المهمة يمكن أن يتوقف.

نفس الفكرة مع:

```text
uber-superset-init
```

---

# 14. اختبار Hadoop

بعد تشغيل الـContainers:

```powershell
docker exec uber-hadoop-master jps
```

المفروض تشوف Processes الخاصة بـHadoop.

اختبر HDFS:

```powershell
docker exec uber-hadoop-master hdfs dfs -ls /
```

وافتح HDFS Web UI:

http://localhost:9870

---

# 15. اختبار Spark

Spark Master UI:

http://localhost:8081

Spark Worker UI:

http://localhost:8082

Jupyter:

http://localhost:8888

---

# 16. اختبار Airflow

Airflow API/Web UI:

http://localhost:8090

للتأكد من الـlogs:

```powershell
docker logs uber-airflow-api-server --tail 50
```

Scheduler:

```powershell
docker logs uber-airflow-scheduler --tail 50
```

---

# 17. اختبار NiFi

NiFi:

https://localhost:8443

> قد يظهر تحذير SSL في المتصفح لأن NiFi يعمل داخل الـDocker environment بإعداد HTTPS.

---

# 18. اختبار Trino

Trino:

http://localhost:8085

---

# 19. اختبار Superset

Superset:

http://localhost:8089

---

# 20. لو حصل Error أثناء Build

لا تعمل:

```powershell
docker compose up -d
```

مباشرة.

حدد أولًا أي Service فشل.

مثلاً لو Hadoop:

```powershell
docker compose build uber-hadoop-master
```

لو Slave:

```powershell
docker compose build uber-hadoop-slave1
```

لو Jupyter:

```powershell
docker compose build uber-jupyter
```

لو Airflow:

```powershell
docker compose build uber-airflow-init
```

لو Superset:

```powershell
docker compose build uber-superset-init
```

ثم ابعت آخر جزء من الـError.

---

# 21. أهم Error في Hadoop

لو ظهر:

```text
pull access denied for uber-hadoop-base-master
```

مع:

```text
FROM uber-hadoop-base-master:latest
```

معناه أن Hadoop Slave يحاول استخدام Master image قبل ما تكون اتبنت محليًا.

الحل:

```powershell
docker compose build uber-hadoop-master
```

ثم:

```powershell
docker compose build uber-hadoop-slave1
docker compose build uber-hadoop-slave2
```

ثم:

```powershell
docker compose up -d
```

---

# 22. لو أردت إعادة Build من البداية

استخدم:

```powershell
docker compose build --no-cache uber-hadoop-master
```

ثم:

```powershell
docker compose build --no-cache uber-hadoop-slave1
docker compose build --no-cache uber-hadoop-slave2
```

ولا تستخدم `--no-cache` إلا عند الحاجة لأنه يجعل الـBuild أبطأ.

---

# 23. لو أردت إيقاف المشروع

```powershell
docker compose down
```

هذا يوقف ويحذف الـContainers والـNetwork الخاصة بالـCompose، لكنه لا يحذف الـnamed volumes افتراضيًا.

---

# 24. لو أردت إيقاف وحذف Volumes أيضًا

⚠️ **استخدم هذا بحذر** لأن الـVolumes قد تحتوي على بيانات المشروع وقواعد البيانات.

```powershell
docker compose down -v
```

هذا يحذف أيضًا الـVolumes الخاصة بالـCompose.

---

# 25. التسلسل المختصر الذي تحفظه

بعد تجهيز المشروع لأول مرة:

```powershell
cd D:\course\Projects\_Data\uber-data-platform
```

### 1 — تحميل Hadoop

```powershell
Invoke-WebRequest `
  -Uri "https://archive.apache.org/dist/hadoop/common/hadoop-3.3.6/hadoop-3.3.6.tar.gz" `
  -OutFile ".\docker\hadoop\hadoop-3.3.6.tar.gz"
```

### 2 — Build Hadoop Master

```powershell
docker compose build uber-hadoop-master
```

### 3 — Build Hadoop Slaves

```powershell
docker compose build uber-hadoop-slave1
docker compose build uber-hadoop-slave2
```

### 4 — Build Jupyter

```powershell
docker compose build uber-jupyter
```

### 5 — Build Airflow

```powershell
docker compose build uber-airflow-init
```

### 6 — Build Superset

```powershell
docker compose build uber-superset-init
```

### 7 — تشغيل المشروع

```powershell
docker compose up -d
```

### 8 — التأكد

```powershell
docker compose ps
```

---

# Architecture بعد التشغيل

```text
                       ┌──────────────┐
                       │    NiFi      │
                       │  Ingestion   │
                       └──────┬───────┘
                              │
                              ▼
                       ┌──────────────┐
                       │     HDFS     │
                       │    Bronze    │
                       └──────┬───────┘
                              │
                              ▼
                       ┌──────────────┐
                       │    Spark     │
                       │    Batch     │
                       └──────┬───────┘
                              │
                              ▼
                       ┌──────────────┐
                       │ HDFS Silver  │
                       └──────┬───────┘
                              │
                              ▼
                       ┌──────────────┐
                       │    Spark     │
                       │ Transformation│
                       └──────┬───────┘
                              │
                              ▼
                       ┌──────────────┐
                       │  Hive/Gold   │
                       └──────┬───────┘
                              │
                              ▼
                       ┌──────────────┐
                       │    Trino     │
                       └──────┬───────┘
                              │
                              ▼
                       ┌──────────────┐
                       │   Superset   │
                       │ Dashboards   │
                       └──────────────┘

                    Airflow = Orchestration
```

---

## References

- Apache Hadoop 3.3.6 archive:
  https://archive.apache.org/dist/hadoop/common/hadoop-3.3.6/

- Docker Compose project configuration is the source used to identify the project's build services, images, ports, volumes, and dependencies.
