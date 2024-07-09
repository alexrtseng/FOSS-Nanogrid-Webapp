import pandas as pd


# Given df of pv predictions and df of load predictions, return pandas df with net load as column
def calc_net_load(
    pv_predictions: pd.DataFrame, load_predictions: pd.DataFrame
) -> pd.Series:
    df = pd.merge(
        pv_predictions[["datetime", "pv_pred"]],
        load_predictions[["datetime", "load_pred"]],
        on="datetime",
        how="inner",
    )
    df["net_load"] = df["load_pred"] - df["pv_pred"]
    return df


# Given df of pv predictions and df of load predictions, return dict of predictions with general info as well
def preds_to_net_load_dict(
    pv_predictions: pd.DataFrame,
    load_predictions: pd.DataFrame,
    sm_name,
    pv_name,
    latitude,
    longitude,
    pv_model="XGBoost_pv_v1",
    load_model="XGBoost_load_v4",
) -> dict:
    df = calc_net_load(pv_predictions, load_predictions)
    values = []
    for _, row in df.iterrows():
        values.append(
            {
                "Timestamp": row["datetime"],
                "PV": row["pv_pred"],
                "Load": row["load_pred"],
                "Net-Load": row["net_load"],
            }
        )

    net_load_dict = {
        "Grid": "UCY Microgrid",
        "Reference SM": sm_name,
        "PV": pv_name,
        "latitude": latitude,
        "longitude": longitude,
        "unit": "MW",
        "PV Model": pv_model,
        "Load Model": load_model,
        "Timezone": "Asia/Nicosia",
        "date_run": pd.Timestamp.now(tz="Asia/Nicosia"),
        "forecasted_dates": f"{values[0]['Timestamp']} to {values[-1]['Timestamp']}",
        "values": values,
    }

    return net_load_dict
