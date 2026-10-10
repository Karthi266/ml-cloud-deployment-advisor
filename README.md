# ML Cloud Deployment Advisor

An ML-powered decision-support system that analyzes machine learning models and workload characteristics to recommend a suitable cloud deployment strategy.

The system evaluates **self-managed virtual machines** and **managed/serverless platforms** using workload characteristics, model information, cloud compatibility, pricing data, cost comparison, benchmarking, and break-even analysis.

---

## Project Overview

Deploying a machine learning model to the cloud is not simply a matter of choosing a cloud provider.

Different workloads have different requirements based on:

- Request volume
- Traffic pattern
- Request duration
- Concurrency
- Latency requirements
- Model size
- Number of model features
- Execution characteristics
- Infrastructure cost

Choosing the wrong deployment strategy can result in unnecessary infrastructure costs, poor scalability, or unsuitable performance characteristics.

This project aims to provide a structured way to evaluate these factors before selecting a deployment strategy.

### High-Level Workflow

```text
                ML MODEL
                    +
               WORKLOAD
                    │
                    ▼
        ┌──────────────────────┐
        │    Model Analysis    │
        └──────────────────────┘
                    │
                    ▼
        ┌──────────────────────┐
        │   Workload Analysis  │
        └──────────────────────┘
                    │
                    ▼
        ┌──────────────────────┐
        │ Deployment Decision  │
        └──────────────────────┘
                    │
            ┌───────┴────────┐
            ▼                ▼
          VM              Cloud
            │                │
            │        ┌───────┴────────┐
            │        │                │
            ▼        ▼                ▼
          AWS     AWS Lambda     Azure Functions
          EC2
          Azure       Google       Google
           VM         Cloud Run    Cloud Run
          GCE
            │                │
            └───────┬────────┘
                    ▼
          Cost & Break-Even
                    │
                    ▼
              Benchmarking
                    │
                    ▼
             Recommendation
```

---

# Key Features

## 1. ML Model Analysis

The system accepts a trained machine learning model and extracts relevant information such as:

- Model type
- Model size
- Number of features
- Number of classes
- Pipeline information
- Supported model characteristics

The current implementation primarily targets Python/scikit-learn style models stored using `.joblib` or `.pkl`.

---

## 2. Workload Analysis

Users can provide workload characteristics including:

- Traffic pattern
  - Steady
  - Bursty
- Expected monthly request volume
- Latency requirement
  - Standard
  - Critical
- Average request duration
- Expected concurrency

These characteristics are used by the deployment decision and evaluation engines.

---

## 3. VM vs Serverless Evaluation

The system compares two major deployment strategies:

### Self-Managed VM

Examples:

- Amazon EC2
- Azure Virtual Machines
- Google Compute Engine

VM-based deployment provides continuously available compute resources and greater control over the runtime environment.

### Managed / Serverless

Examples:

- AWS Lambda
- Azure Functions
- Google Cloud Run

Serverless and managed platforms can provide elastic execution and usage-based pricing depending on the workload.

---

## 4. Cloud Provider Compatibility

The system evaluates whether a workload is compatible with supported managed platforms.

Currently considered platforms include:

| Provider | Managed Platform |
|---|---|
| AWS | AWS Lambda |
| Microsoft Azure | Azure Functions |
| Google Cloud | Google Cloud Run |

Compatibility analysis considers workload characteristics such as:

- Execution duration
- Memory requirements
- Concurrency
- Traffic pattern
- Platform execution limits

---

## 5. Cloud Pricing Analysis

The project contains pricing modules for multiple cloud providers.

The system can estimate monthly deployment costs using factors such as:

- Request volume
- Execution duration
- Memory requirements
- Compute usage
- Provider pricing

Supported pricing areas include:

- AWS Lambda
- Azure Functions
- Google Cloud Run
- AWS EC2
- Azure Virtual Machines
- Google Compute Engine

The project also contains pricing snapshots and supporting pricing data under:

```text
pricing/data/
```

Pricing information is used as an input to the cost comparison and recommendation process.

> Cloud pricing changes frequently. The estimates produced by this project should therefore be treated as decision-support estimates rather than guaranteed cloud bills.

---

## 6. Cost Comparison

The cost comparison engine evaluates:

```text
VM Deployment Cost
        vs
Serverless / Managed Deployment Cost
```

The system identifies the lowest-cost compatible option based on the current pricing model.

---

## 7. Break-Even Analysis

The project includes a break-even analysis engine to determine approximately where the preferred deployment strategy may change as workload volume increases.

For example:

```text
Low Request Volume
       │
       ▼
Serverless may be more economical
       │
       │
       ▼
Request Volume increases
       │
       ▼
Break-Even Region
       │
       ▼
VM may become more economical
```

This allows the system to evaluate deployment strategy as a function of workload rather than making a decision for only one workload size.

---

## 8. Workload Scenario Evaluation

The project includes workload scenario simulation to evaluate different workload conditions.

Example scenarios can vary:

- Request volume
- Traffic pattern
- Concurrency
- Execution characteristics

This helps analyze how deployment recommendations can change under different workload conditions.

---

## 9. Strategy Evaluation

The strategy evaluation engine considers:

- Traffic pattern
- Request volume
- Request duration
- Concurrency
- Latency requirements
- Cost

Strategies considered include:

```text
VM
Serverless
Hybrid
```

The current Hybrid strategy is an evaluation concept and does not represent a complete production hybrid deployment implementation.

---

## 10. Local ML Benchmarking

The project contains a benchmarking engine for measuring model execution characteristics.

Metrics include:

- Average latency
- P50 latency
- P95 latency
- Throughput
- Success rate
- Error rate

Example benchmark metrics:

```text
Requests        : 1000
Concurrency     : 10
Average Latency : ~2.98 ms
P50 Latency     : ~1.63 ms
P95 Latency     : ~6.45 ms
Throughput      : ~3283 req/sec
Success Rate    : 100%
Error Rate      : 0%
```

> These are local model-execution benchmark results. They should not be interpreted as direct measurements of AWS, Azure, or Google Cloud performance.

---

# Decision-Making Architecture

The project separates the decision process into multiple components.

```text
Model
  │
  ▼
Model Analyzer
  │
  ▼
Workload Analyzer
  │
  ▼
Deployment Decision
  │
  ├───────────────┐
  ▼               ▼
VM Evaluation   Cloud Evaluation
  │               │
  ▼               ▼
VM Pricing      Cloud Pricing
  │               │
  └───────┬───────┘
          ▼
   Cost Comparison
          │
          ▼
   Break-Even Analysis
          │
          ▼
      Benchmark
          │
          ▼
   Final Recommendation
```

---

# Project Structure

```text
ml-cloud-deployment-advisor/
│
├── README.md
├── requirements.txt
├── .gitignore
│
├── app/
│   ├── __init__.py
│   ├── advisor.py
│   └── frontend_pro.py
│
├── core/
│   ├── __init__.py
│   ├── model_analyzer.py
│   ├── workload_analyzer.py
│   ├── deployment_decision.py
│   ├── cloud_provider_advisor.py
│   ├── vm_provider_advisor.py
│   ├── recommendation_engine.py
│   ├── break_even_engine.py
│   ├── benchmark_engine.py
│   ├── threshold_analyzer.py
│   ├── strategy_evaluator.py
│   └── scenario_evaluator.py
│
├── pricing/
│   ├── __init__.py
│   ├── aws_ec2_pricing.py
│   ├── aws_pricing.py
│   ├── azure_functions_pricing.py
│   ├── azure_pricing.py
│   ├── cost_calculator.py
│   ├── cost_comparison.py
│   ├── google_cloud_pricing.py
│   ├── google_vm_pricing.py
│   ├── pricing_cache.py
│   ├── pricing_config.py
│   ├── vm_cost_calculator.py
│   │
│   └── data/
│       ├── aws_ec2_price_history.csv
│       ├── aws_lambda_pricing_snapshot.json
│       ├── azure pricing data
│       ├── google_cloud_pricing_snapshot.json
│       ├── google_vm_pricing_snapshot.json
│       ├── ec2_2026_09.json
│       └── index.json
│
├── simulation/
│   ├── __init__.py
│   ├── workload_simulator.py
│   └── workload_scenario_simulator.py
│
├── models/
│   ├── __init__.py
│   └── train_model.py
│
├── tests/
    ├── __init__.py
    └── test_trucost.py
```

---

# Technologies Used

### Programming

- Python

### Machine Learning

- Scikit-learn
- Joblib
- Multinomial Naive Bayes
- CountVectorizer
- ML Pipelines

### Application

- Streamlit

### Cloud Platforms

- Amazon Web Services
- Microsoft Azure
- Google Cloud

### Cloud Services Evaluated

- AWS Lambda
- AWS EC2
- Azure Functions
- Azure Virtual Machines
- Google Cloud Run
- Google Compute Engine

### APIs / Data

- Cloud provider pricing APIs
- JSON pricing snapshots
- CSV pricing history

### Testing / Benchmarking

- Python benchmarking
- Requests
- BeautifulSoup

---

# Reference ML Model

The repository uses a spam-classification model as a reference/test model.

Dataset characteristics:

```text
Total Messages : 5574

Normal         : 4827
Spam           : 747
```

Training/testing split:

```text
Training : 4459
Testing  : 1115
```

Reference model:

```text
CountVectorizer
       ↓
MultinomialNB
```

Evaluation:

```text
Accuracy  : 98.48%
Precision : 97.83%
Recall    : 90.60%
F1 Score  : 94.08%
```

The reference model is used for demonstrating the advisor workflow. The system is designed around accepting model information rather than being limited to spam classification.

---

# Running the Project

## 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/ml-cloud-deployment-advisor.git
```

```bash
cd ml-cloud-deployment-advisor
```

---

## 2. Create a virtual environment

### Windows

```bash
python -m venv venv
```

Activate it:

```bash
venv\Scripts\activate
```

### Linux / macOS

```bash
python3 -m venv venv
```

```bash
source venv/bin/activate
```

---

## 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

## 4. Run the Streamlit application

From the project root:

```bash
streamlit run app/frontend_pro.py
```

The application should open at:

```text
http://localhost:8501
```

---

# Application Workflow

The Streamlit application follows the workflow:

```text
Upload ML Model
       ↓
Model Analysis
       ↓
Workload Configuration
       ↓
Workload Analysis
       ↓
Deployment Decision
       ↓
Cloud Provider Evaluation
       ↓
Cost Analysis
       ↓
Break-Even Analysis
       ↓
Benchmarking
       ↓
Final Recommendation
```

---

# Example Workload

Example input:

```text
Traffic Pattern       : steady
Monthly Requests      : 100000
Latency Requirement   : standard
Request Duration      : 0.2 seconds
Expected Concurrency  : 10
```

The advisor evaluates this workload against available deployment strategies and pricing information.

---

# 🔐 AWS Pricing API

The AWS EC2 pricing module can use AWS pricing APIs through `boto3`.

If AWS credentials are required for a particular pricing operation, configure your AWS credentials using the standard AWS configuration mechanism.

Do not commit credentials, access keys, secret keys, or `.env` files to the repository.

---

# Future Enhancements

## Multi-Framework Model Support

Extend model analysis to:

- TensorFlow
- PyTorch
- XGBoost
- ONNX
- Hugging Face models

---

## Real Cloud Benchmarking

Deploy the same model to selected cloud platforms and compare:

- Cold-start latency
- Warm latency
- P50/P95/P99 latency
- Throughput
- Error rate
- Cost per request

---

## Dynamic Workload Monitoring

Continuously monitor:

```text
Request Volume
      ↓
Concurrency
      ↓
Latency
      ↓
Cost
      ↓
Resource Utilization
```

and determine whether the current deployment strategy remains optimal.

---

## Dynamic Strategy Recommendation

Future versions can detect workload changes and recommend:

```text
Serverless
    ↕
VM
    ↕
Hybrid
```

based on measured workload thresholds.

---

## Automated Deployment

Future versions may integrate deployment automation for selected cloud platforms.

---

## Multi-Cloud Benchmarking

Run the same model and workload across:

```text
AWS
Azure
Google Cloud
```

and compare real measured performance and cost.

---
