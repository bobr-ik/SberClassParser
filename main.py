import json
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import os
import math
from statistics import mean, median, mode, stdev
from parce_sberclass import get_marks


YOUR_LOGIN = "ваш_логин"
YOUR_PASSWORD = "ваш_пароль"



def classic_round(n):
    return int(math.floor(n + 0.5))

def add_overall_average(stats, all_marks):
    avg = round(sum(all_marks) / len(all_marks), 2) if all_marks else 0
    stats.append(f"# **ИТОГОВЫЙ СРЕДНИЙ БАЛЛ: {avg:.2f}**\n")


os.makedirs("report_dir/plots", exist_ok=True)

subjects = get_marks(YOUR_LOGIN, YOUR_PASSWORD)
with open("report_dir/grades.json", "w+", encoding="utf-8") as f:
    for i in range(len(subjects)):
        subjects[i] = subjects[i].model_dump()
    json.dump(subjects, f, indent=4, ensure_ascii=False)

# # Загрузка JSON (Чтобы не парсить каждый раз)
# with open("report_dir/grades.json", "r", encoding="utf-8") as f:
#     subjects = json.load(f)



stats = []
global_marks = []

stats.append("# 📊 Отчет по оценкам\n")

def weighted_avg(marks):
    return round(sum(m * k for m, k in marks) / sum(k for _, k in marks), 2) if marks else 0

def calc_school_mark(avg):
    if avg is None or avg == "-" or avg == 0:
        return "-"
    base = int(avg)
    fraction = avg - base
    return base + 1 if fraction >= 0.6 else base

# Собираем все оценки для общей гистограммы
for subj in subjects:
    for module in subj["modules"]:
        for entry in module["marks"]:
            mark = entry["mark"]
            koef = entry["koef"]
            global_marks.extend([mark] * koef)

# Строим общую гистограмму
plt.figure(figsize=(6, 4))
plt.hist(global_marks, bins=np.arange(1.5, 6.6, 1), edgecolor='black', color="salmon", rwidth=0.8)
plt.title("Общая гистограмма оценок")
plt.xlabel("Оценка")
plt.ylabel("Частота")
plt.xticks([2, 3, 4, 5])
plt.tight_layout()
global_img = "report_dir/plots/summary_hist.png"
plt.savefig(global_img)
plt.close()

from collections import Counter

def summarize(marks):
    return {
        "Средняя": round(mean(marks), 2),
        "Медиана": round(np.median(marks), 2),
        "Мода": Counter(marks).most_common(1)[0][0] if marks else None,
        "Количество": len(marks),
        "Распределение": dict(Counter(marks))
    }


global_summary = summarize(global_marks)
stats.append(f"![Общая гистограмма](/{global_img})\n")
stats.append("## Все предметы — статистика\n")
stats.append(f"- Средняя: **{global_summary['Средняя']}**\n")
stats.append(f"- Медиана: **{global_summary['Медиана']}**\n")
stats.append(f"- Мода: **{global_summary['Мода']}**\n")
stats.append(f"- Кол-во оценок: **{global_summary['Количество']}**\n")
stats.append("- Распределение:\n")
for k in sorted([2, 3, 4, 5]):
    stats.append(f"  - Оценка ***{k}***: {global_summary['Распределение'].get(k, 0)} шт.\n")

add_overall_average(stats, global_marks)
# Формируем итоговую таблицу
final_rows = []

global_marks = []
rows = []
for subj in subjects:
    name = subj["name"]
    module_avgs = {}
    flat_all_marks = []

    # Собираем средние по модулям
    for module in subj["modules"]:
        marks = []
        for entry in module["marks"]:
            mark = entry["mark"]
            koef = entry["koef"]
            marks.extend([mark] * koef)
            flat_all_marks.append((mark, koef))
        if marks:
            avg = round(sum(marks) / len(marks), 2)
            module_avgs[module["name"]] = avg
        else:
            module_avgs[module["name"]] = None

    # Берём средние по модулю 1 и 2 (если отсутствуют, "-")
    mod1_avg = module_avgs.get("1", None)
    mod2_avg = module_avgs.get("2", None)

    mod1_mark = calc_school_mark(mod1_avg) if mod1_avg is not None else "-"
    mod2_mark = calc_school_mark(mod2_avg) if mod2_avg is not None else "-"
    # Итоговая оценка за год — математическое округление среднего двух модулей

    if mod1_avg is not None and mod2_avg is not None:
        year_avg = round((mod1_avg + mod2_avg) / 2, 2)
        year_mark = classic_round((mod1_mark + mod2_mark) / 2)
    elif mod1_avg is not None:
        year_avg = mod1_avg
        year_mark = mod1_mark
    elif mod2_avg is not None:
        year_avg = mod2_avg
        year_mark = mod2_mark
    else:
        year_avg = "-"
        year_mark = "-"


    final_rows.append({
        "Предмет": name,
        "I Модуль": f"{mod1_avg:.2f}" if mod1_avg is not None else "-",
        "Оценка за I модуль": mod1_mark,
        "II Модуль": f"{mod2_avg:.2f}" if mod2_avg is not None else "-",
        "Оценка за II модуль": mod2_mark,
        "Год": f"{year_avg:.2f}" if year_avg != "-" else "-",
        "Оценка за год": year_mark
    })

df_final = pd.DataFrame(final_rows)



stats.append("\n## 📋 Итоговая таблица оценок\n")
stats.append(df_final.to_markdown(index=False))




def summarize(marks):
    return {
        "Средняя": round(mean(marks), 2),
        "Медиана": median(marks),
        "Мода": mode(marks),
        "Ст. отклонение": round(stdev(marks), 2) if len(marks) > 1 else 0,
        "Количество": len(marks),
        "По баллам": dict(Counter(marks))
    }

def format_summary(title, summary):
    s = ''
    s += f"- 📈 Средняя: **{summary['Средняя']}**\n"
    s += f"- 📊 Медиана: **{summary['Медиана']}**\n"
    s += f"- 🥇 Мода: **{summary['Мода']}**\n"
    s += f"- 📉 Ст. отклонение: **{summary['Ст. отклонение']}**\n"
    s += f"- 🧮 Кол-во оценок: **{summary['Количество']}**\n"
    s += "- 🧾 Распределение:\n"
    for k in sorted([2, 3, 4, 5]):
        s += f"  - Оценка {k}: {summary['По баллам'].get(k, 0)} шт.\n"
    return s + "\n"

def weighted_avg(marks):
    return round(sum(m * k for m, k in marks) / sum(k for _, k in marks), 2)

# Анализ предметов
for subj in subjects:
    name = subj["name"].replace(' ', '_')
    subject_marks = []
    flat_marks = []

    for module in subj["modules"]:
        module_name = module["name"]
        marks = []
        for entry in module["marks"]:
            mark = entry["mark"]
            koef = entry["koef"]
            marks.extend([mark] * koef)
            subject_marks.extend([mark] * koef)
            flat_marks.append((mark, koef))
            global_marks.extend([mark] * koef)

        rows.append({
            "Предмет": name,
            "Модуль": module_name,
            "Оценки": ", ".join(map(str, marks)),
            "Средняя (взвеш.)": round(sum(marks) / len(marks), 2)
        })
    if not(subject_marks): continue

    # График
    plt.figure(figsize=(6, 4))
    plt.hist(subject_marks, bins=np.arange(1.5, 6.6, 1), edgecolor='black', color="skyblue", rwidth=0.8)
    plt.title(f"{name} — гистограмма оценок")
    plt.xlabel("Оценка")
    plt.ylabel("Частота")
    plt.xticks([2, 3, 4, 5])
    plt.tight_layout()
    img_path = f"report_dir/plots/{name}_hist.png"
    plt.savefig(img_path)
    plt.close()

    # Отчёт
    stats.append(f"## {name}\n")
    summary = summarize(subject_marks)
    stats.append(format_summary(name, summary))
    stats.append(f"![{name}](/{img_path})\n")

    # Строка с итогом за год
    avg_year = weighted_avg(flat_marks)
    rows.append({
        "Предмет": name,
        "Модуль": "🟢 Итог",
        "Оценки": "—",
        "Средняя (взвеш.)": avg_year
    })

with open("report_dir/report.md", "w", encoding="utf-8") as f:
    f.write("\n".join(stats))

print("✅ Отчет обновлён: report.md + графики в plots/")
