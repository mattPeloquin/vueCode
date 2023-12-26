
# Cloudwatch metrics

Don't use detailed monitoring with EC2, capture metrics explicitly with CWAgent for more control.

https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/metrics-collected-by-CloudWatch-agent.html


Potential CPU valuesS

    "cpu_usage_iowait",
    "cpu_usage_user",
    "cpu_usage_system",


Old Dashboard for EC2 CPU metrics

                    [ "AWS/EC2", "CPUUtilization", "AutoScalingGroupName", "prodA", { "yAxis": "left", "label": "prodA" } ],
                    [ "...", "prod-boh", { "label": "prod-boh", "color": "#2ca02c", "yAxis": "right" } ],
                    [ "...", "prod-ft", { "color": "#9467bd", "yAxis": "left" } ],
                    [ "...", "prod-osk", { "color": "#7f7f7f", "yAxis": "right" } ],
                    [ "...", "prod-mpd", { "label": "dev", "color": "#f7b6d2", "yAxis": "right" } ]
