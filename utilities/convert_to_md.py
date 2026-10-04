import json
import os
from collections import defaultdict


def json_to_markdown(
    json_path="question_bank.json", md_path="question_bank.md"
):
    # Fallback to question_bank.json if extracted_questions.json is not found
    if not os.path.exists(json_path):
        if os.path.exists("question_bank.json"):
            json_path = "question_bank.json"
        else:
            print(f"Error: Neither {json_path} nor question_bank.json found.")
            return

    with open(json_path, "r", encoding="utf-8") as f:
        questions = json.load(f)

    # Group questions by section/module
    grouped = defaultdict(list)
    for q in questions:
        section = q.get("section", "General Assessment").strip()
        grouped[section].append(q)

    with open(md_path, "w", encoding="utf-8") as out:
        out.write("# AI Governance Question Bank & Study Reference\n\n")
        out.write(
            f"*Total Questions: {len(questions)} across {len(grouped)} sections.*\n\n"
        )
        out.write("---\n\n")

        for section_title, q_list in grouped.items():
            out.write(f"## {section_title}\n\n")

            for idx, q in enumerate(q_list, start=1):
                q_num = q.get("question_number") or f"Q{idx}"
                q_text = q.get("question", "").strip()
                options = q.get("options", [])
                correct_ans = q.get("correct_answer", "").strip()
                explanation = q.get("explanation", "").strip()

                out.write(f"### {q_num}: {q_text}\n\n")
                out.write("**Options:**\n")

                for opt in options:
                    opt_clean = opt.strip()
                    if opt_clean == correct_ans:
                        # Highlight the correct answer clearly for NotebookLM ingestion
                        out.write(f"- [x] **{opt_clean}** *(Correct)*\n")
                    else:
                        out.write(f"- [ ] {opt_clean}\n")

                out.write("\n")
                out.write(f"**Answer:** {correct_ans}\n\n")

                if explanation:
                    # Format explanation in a blockquote for clear semantic separation
                    out.write(f"> **Explanation:** {explanation}\n\n")

                out.write("---\n\n")

    print(
        f"Successfully converted {len(questions)} questions to '{md_path}'!"
    )


if __name__ == "__main__":
    json_to_markdown()
