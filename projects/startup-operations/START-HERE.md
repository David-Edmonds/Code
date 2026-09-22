# Startup Operations Dashboards

Seven editable Tableau dashboards for exploring startup operations: service availability, product releases, acquisition and activation, waitlist movement, recurring revenue, backend reliability, and frontend performance.

This independent demonstration uses fictional Northstar data: 184 daily records covering March–August 2026, 26 releases, and eight resolved incidents. It does not describe a real company's results.

## Explore

Open index.html for seven screenshots captured from Tableau. Download Startup-Operations-Expanded.twbx and open it in Tableau to use the reporting-month selector and edit the native worksheets. Both data extracts are packaged inside the workbook.

The workbook contains seven dashboards, 70 worksheets, 21 headline metrics with comparisons, 14 trend charts, and 14 operational detail panels. Segoe UI typography and a navy, teal, and slate palette provide a consistent visual hierarchy.

## Analytical approach

Rates use aggregated numerators and denominators. MRR, customers, and waiting-list balances are ending observations rather than summed daily balances. Opening-to-ending MRR and waitlist movements reconcile. Monthly headline reconciliation checked 126 sample values.

MRR is a recurring run rate; receipts represent cash collection. Waitlist throughput is not cohort conversion. Frontend figures are daily p75 observations and must not be interpreted as monthly percentiles or a 28-day Core Web Vitals assessment.

## Scope

The web gallery contains static screenshots. Interactive controls are in the downloaded Tableau workbook. This is a synthetic-data template, not a live status service, alert system, or production integration. Supporting details are precomputed and must be regenerated together with the daily extract when source data changes. This showcase does not include the refresh toolkit.

## Suggested project listing

**Startup Operations Dashboards | Tableau**

Explore seven connected operational views with monthly KPI comparisons, reconciled revenue and waitlist movements, incident and release detail, and performance trends. Built with synthetic data and packaged as an editable Tableau workbook.
