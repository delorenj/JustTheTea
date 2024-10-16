export interface DashboardData {
  date_range: {
    start: string;
    end: string;
  };
  team_metrics: {
    prs_merged: number;
    merge_conflicts_resolved: number;
    lines_of_code: number;
    average_review_time: number;
  };
  highlights: {
    icon: string;
    content: string;
  }[];
}
