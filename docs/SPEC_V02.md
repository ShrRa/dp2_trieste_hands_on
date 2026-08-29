# SPEC_V02

Refactoring the code after SPEC_V01 was implemented.
Desiderata:
 - Objects with >10 nDiaSources mostly have 30-40 observations tops, and are still hard to judge visually. We need to prepare the sample with >100 nDiaSources - we'll probably be able to store all of them as a new collection.
 - Whenever possible, we should store new data as new columns in the same collection, not as new tables.
 - An event detection functionality needed (use something from Mallorn?)
 - There are already some 'features' calculated in diaObject (e.g fluxSlope). It is unlikely they are very useful since they are calculated without outliers filtering, but still worth exploring.
 - Look for the photometric scatter issue.
