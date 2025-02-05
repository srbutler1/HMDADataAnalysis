import pandas as pd

class VisualizationAgent:
    def __init__(self, fig):
        """Initialize with a Plotly figure object"""
        self.fig = fig

    def analyze_figure(self):
        """Analyze the Plotly figure and provide insights"""
        if not self.fig:
            return "No valid figure provided."

        insights = []
        
        # Get the plot type and title
        plot_type = self.fig.data[0].type if self.fig.data else "unknown"
        title = self.fig.layout.title.text if hasattr(self.fig.layout, 'title') else "Untitled"
        insights.append(f"Plot Type: {plot_type}")
        insights.append(f"Title: {title}")

        # Analyze based on plot type
        if plot_type == 'bar':
            # Extract x and y values
            trace = self.fig.data[0]
            if hasattr(trace, 'x') and hasattr(trace, 'y'):
                # Create a list of (x, y) pairs
                data_pairs = list(zip(trace.x, trace.y))
                # Sort by y values in descending order
                data_pairs.sort(key=lambda x: x[1], reverse=True)
                
                # Report top 5 values
                insights.append("\nTop 5 Areas by Value:")
                for i, (area, value) in enumerate(data_pairs[:5], 1):
                    insights.append(f"{i}. {area}: {value:,.2f}")
                
                # Basic statistics
                y_values = trace.y
                insights.append(f"\nSummary Statistics:")
                insights.append(f"Maximum Value: {max(y_values):,.2f}")
                insights.append(f"Minimum Value: {min(y_values):,.2f}")
                insights.append(f"Average Value: {sum(y_values)/len(y_values):,.2f}")

        elif plot_type == 'box':
            trace = self.fig.data[0]
            if hasattr(trace, 'y'):
                y_values = trace.y
                insights.append("\nDistribution Analysis:")
                insights.append(f"Median: {pd.Series(y_values).median():,.2f}")
                insights.append(f"Q1 (25th percentile): {pd.Series(y_values).quantile(0.25):,.2f}")
                insights.append(f"Q3 (75th percentile): {pd.Series(y_values).quantile(0.75):,.2f}")

        return "\n".join(insights)
