import arrow

date = arrow.get("1 Oct 1947", ["DD MMM YYYY", "D MMM YYYY"])
print(date.format("DD/MM/YYYY"))
print(date)