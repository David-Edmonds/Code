# Expanded design specifications

The expanded edition uses a compact 1200 × 820 desktop canvas with a navy masthead, white cards on pale slate, and only seven navigation tabs. Segoe UI remains the single font family: 24 pt main headings, 27 pt headline values, 12 pt chart/panel titles, 11 pt detail text, 10 pt comparisons and 9 pt scope notes. Left alignment connects each KPI label, value and change.

Colours: navy #132D46; ink #18324B; supporting slate #526579; pale canvas #F1F5F9; white #FFFFFF; primary chart teal #087F8C; supporting chart slate-blue #526D93. Colour separates visual emphasis, not good/bad states. The original palette's text contrast checks passed; do not use pale tints for important numbers.

A 26 px margin frames three 372 px KPI cards, two 566 px trend panels, and two 566 px operational-detail panels. Hide helper tabs while keeping all native worksheets editable. Charts retain six months; the card changes and detail panels follow the shared reporting parameter. Keep month labels horizontal. Bars start at zero; uptime uses a labelled focused percentage scale. Monetary receipts retain cents.

The new detail panels are native Tableau text worksheets driven by a derived source, not baked images. Regenerate both extracts with the supplied helper when changing source data. Add fields, charts or rows only when they answer a distinct operational question; preserve the reading order from status to history to explanatory detail.
