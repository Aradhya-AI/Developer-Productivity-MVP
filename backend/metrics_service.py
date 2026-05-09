import os
from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DATA_PATH = BASE_DIR / "data" / "developer_productivity_data.xlsx"
DATA_PATH = Path(os.environ.get("DATA_PATH", DEFAULT_DATA_PATH)).resolve()


class MetricsService:
    """Loads the workbook and builds the IC dashboard response."""

    def __init__(self, data_path=DATA_PATH):
        self.data_path = data_path
        self._load_data()

    def _load_data(self):
        if not self.data_path.exists():
            raise FileNotFoundError(
                f"Excel workbook not found at {self.data_path}. "
                "Ensure backend/data/developer_productivity_data.xlsx is committed "
                "or set DATA_PATH to the workbook location."
            )

        workbook = pd.ExcelFile(self.data_path)
        self.developers = pd.read_excel(workbook, "Dim_Developers")
        self.issues = pd.read_excel(workbook, "Fact_Jira_Issues")
        self.pull_requests = pd.read_excel(workbook, "Fact_Pull_Requests")
        self.deployments = pd.read_excel(workbook, "Fact_CI_Deployments")
        self.bugs = pd.read_excel(workbook, "Fact_Bug_Reports")

        for frame, columns in [
            (self.issues, ["in_progress_at", "done_at"]),
            (self.pull_requests, ["opened_at", "merged_at", "first_review_at"]),
            (self.deployments, ["completed_at"]),
            (self.bugs, ["found_at"]),
        ]:
            for column in columns:
                frame[column] = pd.to_datetime(frame[column], errors="coerce")

        self.available_months = sorted(
            set(self.issues["month_done"].dropna().astype(str))
            | set(self.pull_requests["month_merged"].dropna().astype(str))
            | set(self.deployments["month_deployed"].dropna().astype(str))
            | set(self.bugs["month_found"].dropna().astype(str))
        )

    def get_dashboard(self, developer_id=None, month=None):
        developer_id = developer_id or str(self.developers.iloc[0]["developer_id"])
        month = month or self.available_months[-1]

        developer = self._developer_profile(developer_id)
        current = self._metrics_for(developer_id, month)
        previous_month = self._previous_month(month)
        previous = self._metrics_for(developer_id, previous_month) if previous_month else None

        metrics = [
            self._metric_card(
                key="lead_time_days",
                label="Lead Time for Changes",
                value=current["lead_time_days"],
                suffix="days",
                definition="PR opened to successful production deployment",
                previous_value=previous["lead_time_days"] if previous else None,
                lower_is_better=True,
            ),
            self._metric_card(
                key="cycle_time_days",
                label="Cycle Time",
                value=current["cycle_time_days"],
                suffix="days",
                definition="Issue in progress to done",
                previous_value=previous["cycle_time_days"] if previous else None,
                lower_is_better=True,
            ),
            self._metric_card(
                key="bug_rate",
                label="Bug Rate",
                value=current["bug_rate"],
                suffix="%",
                definition="Bugs divided by completed issues",
                previous_value=previous["bug_rate"] if previous else None,
                lower_is_better=True,
                percent=True,
            ),
            self._metric_card(
                key="deployment_frequency",
                label="Deployment Frequency",
                value=current["deployment_frequency"],
                suffix="deployments",
                definition="Successful production deployments per month",
                previous_value=previous["deployment_frequency"] if previous else None,
            ),
            self._metric_card(
                key="pr_throughput",
                label="PR Throughput",
                value=current["pr_throughput"],
                suffix="merged PRs",
                definition="Merged pull requests per month",
                previous_value=previous["pr_throughput"] if previous else None,
            ),
        ]

        insights = self._build_insights(current, previous)
        actions = self._build_actions(current)

        return {
            "selected": {"developer_id": developer_id, "month": month},
            "developer": developer,
            "metrics": metrics,
            "insights": insights,
            "actions": actions,
            "trend": self._trend(developer_id),
            "options": {
                "developers": self.developers.to_dict(orient="records"),
                "months": self.available_months,
            },
            "raw_counts": current["raw_counts"],
        }

    def _developer_profile(self, developer_id):
        matches = self.developers[self.developers["developer_id"] == developer_id]
        if matches.empty:
            return {}
        row = matches.iloc[0].to_dict()
        return {key: _clean_value(value) for key, value in row.items()}

    def _metrics_for(self, developer_id, month):
        issues = self.issues[
            (self.issues["developer_id"] == developer_id)
            & (self.issues["month_done"].astype(str) == month)
            & (self.issues["status"].str.lower() == "done")
        ].copy()

        prs = self.pull_requests[
            (self.pull_requests["developer_id"] == developer_id)
            & (self.pull_requests["month_merged"].astype(str) == month)
            & (self.pull_requests["status"].str.lower() == "merged")
        ].copy()

        deployments = self.deployments[
            (self.deployments["developer_id"] == developer_id)
            & (self.deployments["month_deployed"].astype(str) == month)
            & (self.deployments["environment"].str.lower() == "prod")
            & (self.deployments["status"].str.lower() == "success")
        ].copy()

        bugs = self.bugs[
            (self.bugs["developer_id"] == developer_id)
            & (self.bugs["month_found"].astype(str) == month)
            & (self.bugs["escaped_to_prod"].astype(str).str.lower() == "yes")
        ].copy()

        lead_source = deployments.merge(
            self.pull_requests[["pr_id", "opened_at"]], on="pr_id", how="left"
        )
        lead_time_days = _mean_days(lead_source["completed_at"] - lead_source["opened_at"])
        cycle_time_days = _mean_days(issues["done_at"] - issues["in_progress_at"])
        completed_issues = int(len(issues))
        bug_count = int(len(bugs))

        return {
            "lead_time_days": lead_time_days,
            "cycle_time_days": cycle_time_days,
            "bug_rate": (bug_count / completed_issues) if completed_issues else 0,
            "deployment_frequency": int(len(deployments)),
            "pr_throughput": int(len(prs)),
            "review_wait_hours": _safe_mean(prs["review_wait_hours"]) if not prs.empty else 0,
            "review_rounds": _safe_mean(prs["review_rounds"]) if not prs.empty else 0,
            "lines_changed": _safe_mean(prs["lines_changed"]) if not prs.empty else 0,
            "bug_root_causes": bugs["root_cause_bucket"].dropna().value_counts().to_dict(),
            "raw_counts": {
                "completed_issues": completed_issues,
                "bugs": bug_count,
                "successful_prod_deployments": int(len(deployments)),
                "merged_prs": int(len(prs)),
            },
        }

    def _metric_card(
        self,
        key,
        label,
        value,
        suffix,
        definition,
        previous_value=None,
        lower_is_better=False,
        percent=False,
    ):
        display_value = round(value * 100, 1) if percent else round(value, 1)
        previous_display = (
            round(previous_value * 100, 1) if percent and previous_value is not None else previous_value
        )
        if previous_display is not None and not percent:
            previous_display = round(previous_display, 1)

        change = None
        signal = "neutral"
        if previous_value is not None:
            delta = value - previous_value
            change = round(delta * 100, 1) if percent else round(delta, 1)
            if abs(change) > 0:
                improved = delta < 0 if lower_is_better else delta > 0
                signal = "good" if improved else "watch"

        return {
            "key": key,
            "label": label,
            "value": display_value,
            "suffix": suffix,
            "definition": definition,
            "previous_value": previous_display,
            "change": change,
            "signal": signal,
        }

    def _build_insights(self, current, previous):
        insights = []
        if current["lead_time_days"] >= 4:
            insights.append(
                "Lead time is the main flow risk this month; work is taking longer to reach production after PRs open."
            )
        elif current["lead_time_days"] > 0:
            insights.append(
                "Lead time is in a healthy range, so changes are reaching production without a long release delay."
            )

        if current["cycle_time_days"] >= 5:
            insights.append(
                "Cycle time is elevated, which points to tickets spending too long between in-progress and done."
            )
        elif current["cycle_time_days"] > 0:
            insights.append(
                "Cycle time looks controlled; once work starts, issues are moving to done steadily."
            )

        if current["bug_rate"] > 0:
            root_cause = _top_key(current["bug_root_causes"])
            detail = f" The most visible cause is {root_cause}." if root_cause else ""
            insights.append(
                f"Bug rate is not zero, so quality needs attention alongside delivery speed.{detail}"
            )
        else:
            insights.append("No escaped production bugs are recorded for this developer in the selected month.")

        if previous:
            if current["pr_throughput"] > previous["pr_throughput"]:
                insights.append("PR throughput increased versus the previous month, showing more completed code flow.")
            elif current["pr_throughput"] < previous["pr_throughput"]:
                insights.append("PR throughput decreased versus the previous month, so capacity or review flow may have dipped.")

        return insights[:4]

    def _build_actions(self, current):
        actions = []
        if current["review_wait_hours"] >= 20:
            actions.append(
                {
                    "title": "Reduce review wait time",
                    "detail": "Ask for earlier reviewer assignment and keep PRs smaller so feedback starts sooner.",
                }
            )
        if current["cycle_time_days"] >= 5:
            actions.append(
                {
                    "title": "Split work before starting",
                    "detail": "Break large issues into thinner slices before moving them to in progress.",
                }
            )
        if current["bug_rate"] > 0:
            actions.append(
                {
                    "title": "Add a quality check around the top bug cause",
                    "detail": "Turn the latest production bug pattern into one regression test or release checklist item.",
                }
            )
        if current["deployment_frequency"] <= 1:
            actions.append(
                {
                    "title": "Increase release rhythm",
                    "detail": "Batch less work per deployment and prefer a predictable weekly production release path.",
                }
            )
        if not actions:
            actions.append(
                {
                    "title": "Keep the current flow visible",
                    "detail": "Continue tracking lead time, cycle time, and bug rate monthly to catch drift early.",
                }
            )
        return actions[:3]

    def _trend(self, developer_id):
        return [self._trend_point(developer_id, month) for month in self.available_months]

    def _trend_point(self, developer_id, month):
        metrics = self._metrics_for(developer_id, month)
        return {
            "month": month,
            "lead_time_days": round(metrics["lead_time_days"], 1),
            "cycle_time_days": round(metrics["cycle_time_days"], 1),
            "bug_rate": round(metrics["bug_rate"] * 100, 1),
            "deployments": metrics["deployment_frequency"],
            "merged_prs": metrics["pr_throughput"],
        }

    def _previous_month(self, month):
        if month not in self.available_months:
            return None
        index = self.available_months.index(month)
        return self.available_months[index - 1] if index > 0 else None


def _mean_days(series):
    if series.empty:
        return 0
    values = series.dropna().dt.total_seconds() / 86400
    return _safe_mean(values)


def _safe_mean(series):
    if len(series) == 0:
        return 0
    value = series.mean()
    return 0 if pd.isna(value) else float(value)


def _top_key(values):
    if not values:
        return None
    return max(values, key=values.get)


def _clean_value(value):
    if pd.isna(value):
        return None
    return value
