"""
CLI entry point for the Passenger Flow Predictor.

Usage:
    python pipeline.py train --schedule data/sample/sample_flights.csv
    python pipeline.py predict --schedule data/sample/sample_flights.csv
    python pipeline.py run --schedule data/sample/sample_flights.csv
    python pipeline.py insights --schedule data/sample/sample_flights.csv
"""

import argparse
import sys
from pathlib import Path


def cmd_train(args):
    from src.data.loader import load_flights
    from src.data.cleaner import clean_flights
    from src.data.features import build_feature_matrix
    from src.model.train import train
    from src.model.evaluate import evaluate

    print(f"Loading schedule: {args.schedule}")
    df = load_flights(args.schedule)
    df = clean_flights(df)
    features = build_feature_matrix(df)

    print(f"Training XGBoost on {len(features)} windows…")
    model = train(features, save=True)

    metrics = evaluate(model, features)
    print(f"Training metrics: {metrics}")


def cmd_predict(args):
    from src.data.loader import load_flights
    from src.model.predict import predict_next_day
    from src.model.train import load_model

    print(f"Loading schedule: {args.schedule}")
    df = load_flights(args.schedule)
    model = load_model()

    predictions = predict_next_day(model, df)
    print("\nPredicted passenger load:")
    print(predictions.to_string(index=False))
    return predictions


def cmd_run(args):
    """Train + predict + generate alerts in one shot."""
    from src.data.loader import load_flights
    from src.data.cleaner import clean_flights
    from src.data.features import build_feature_matrix
    from src.model.train import train
    from src.model.predict import predict
    from src.alerts.engine import generate_alerts
    from src.alerts.state import save_alerts, clear_alerts, init_db

    print(f"Loading schedule: {args.schedule}")
    df = load_flights(args.schedule)
    df = clean_flights(df)
    features = build_feature_matrix(df)

    print("Training model…")
    model = train(features, save=True)

    predictions = predict(model, features)
    print("\nPredictions:")
    print(predictions.to_string(index=False))

    alerts = generate_alerts(predictions)
    print(f"\nGenerated {len(alerts)} alerts:")
    for a in alerts:
        print(f"  [{a['status']}] {a['message']}")

    init_db()
    clear_alerts()
    save_alerts(alerts)
    print("\nAlerts saved to SQLite.")


def cmd_insights(args):
    from src.data.loader import load_flights
    from src.model.predict import predict_next_day
    from src.model.train import load_model
    from src.alerts.state import get_alerts
    from src.llm.insights import get_insights

    df = load_flights(args.schedule)
    model = load_model()
    predictions = predict_next_day(model, df)
    alerts = get_alerts(status="OPEN")

    question = getattr(args, "question", None)
    print("Fetching Claude insights…")
    insight = get_insights(predictions, alerts, question=question)
    print("\n" + insight)


def main():
    parser = argparse.ArgumentParser(description="Passenger Flow Predictor CLI")
    sub = parser.add_subparsers(dest="command")

    for cmd in ["train", "predict", "run", "insights"]:
        p = sub.add_parser(cmd)
        p.add_argument("--schedule", default="data/sample/sample_flights.csv")
        if cmd == "insights":
            p.add_argument("--question", default=None)

    args = parser.parse_args()

    handlers = {
        "train": cmd_train,
        "predict": cmd_predict,
        "run": cmd_run,
        "insights": cmd_insights,
    }

    if args.command not in handlers:
        parser.print_help()
        sys.exit(1)

    handlers[args.command](args)


if __name__ == "__main__":
    main()
