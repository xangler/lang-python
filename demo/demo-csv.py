import csv

Outfile = "demo.csv"

with open(Outfile, 'w', newline='',encoding="utf-8-sig") as fp:
    writer = csv.writer(fp)
    writer.writerow(["科目","分数"])
    writer.writerow(["语文", 84])
    writer.writerow(["数学", 73])