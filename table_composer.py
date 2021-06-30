import logging

import pandas as pd

from src.utility import subjects, tools


def main(root_dir: str = "data_cmp"):
    # valid_tools = [tool for tool in tools if tool != "judy"]
    valid_tools = tools

    dataframes = []

    for subject in subjects:
        for tool in valid_tools:
            csvpath = f"{root_dir}/{subject}/{tool}/{subject}_{tool}.csv"
            df = pd.read_csv(csvpath, index_col=0)

            ddf = pd.DataFrame(df.count(axis=1), columns=["live_count"])
            ddf["Group"] = ddf.index.str.extract(r"(\w\d).*").set_index(ddf.index)
            ddf["Tool"] = tool.capitalize()
            ddf["Project"] = subject.capitalize()

            # calculate effectiveness as 1 - live achieved / live total
            ddf["effectiveness"] = 1 - ddf["live_count"] / ddf["live_count"].max()

            x = (
                ddf.dropna()
                .reset_index(drop=True)
                .set_index(["Tool", "Group", "Project"])
            )
            dataframes.append(x)

    df = pd.concat(dataframes).sort_index()
    df.to_csv(f"{root_dir}/effectiveness.csv")
    print(df)


if __name__ == "__main__":
    logging.basicConfig(
        format="%(levelname)s :: [%(module)s.%(lineno)d] :: %(message)s",
        level=logging.INFO,
    )

    main()
