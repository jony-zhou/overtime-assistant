"""
除錯腳本 - 檢查個人記錄資料流

執行方式:
python debug_personal_records.py

此腳本會模擬資料流並輸出詳細日誌
"""

import logging
from src.parsers.personal_record_parser import PersonalRecordParser

# 設定詳細日誌
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

# 測試 HTML (模擬實際資料)
test_html = """
<table id="ContentPlaceHolder1_gvFlow211">
    <tr class="RowStyle">
        <td>
            <span id="ContentPlaceHolder1_gvFlow211_lblOT_Emp_Name_0">周岳廷</span>
            <br>
            <span id="ContentPlaceHolder1_gvFlow211_lblOT_Date_0">2025/11/27</span>
        </td>
        <td>
            <span id="ContentPlaceHolder1_gvFlow211_lblOT_Dept_Text_0">測試部門</span>
            <br>
            <span id="ContentPlaceHolder1_gvFlow211_lblOT_Describe_0" title="優化資安http連線問題">優化資安http連線問題</span>
        </td>
        <td>
            <span id="ContentPlaceHolder1_gvFlow211_Label9_0">加班</span>
            <br>
            <span id="ContentPlaceHolder1_gvFlow211_lblT_Change_0" style="color:Blue;">調休</span>
        </td>
        <td>
            <span id="ContentPlaceHolder1_gvFlow211_lblOT_Minute_0">0.62</span>&nbsp;
            <br>
            <span id="ContentPlaceHolder1_gvFlow211_lblChange_Minute_0"> </span>&nbsp;
        </td>
        <td><span id="ContentPlaceHolder1_gvFlow211_lblOT_Manhour_0">2.67</span></td>
        <td><span id="ContentPlaceHolder1_gvFlow211_lblOT_Monhour_0">30.67</span></td>
        <td><span id="ContentPlaceHolder1_gvFlow211_lblProcess_Flag_Text_0">簽核完成</span></td>
    </tr>
    <tr class="AlternatingRowStyle_update">
        <td>
            <span id="ContentPlaceHolder1_gvFlow211_lblOT_Emp_Name_1">周岳廷</span>
            <br>
            <span id="ContentPlaceHolder1_gvFlow211_lblOT_Date_1">2025/11/26</span>
        </td>
        <td>
            <span id="ContentPlaceHolder1_gvFlow211_lblOT_Dept_Text_1">測試部門</span>
            <br>
            <span id="ContentPlaceHolder1_gvFlow211_lblOT_Describe_1" title="開發報工系統 限制設定功能">開發報工系統 限制設定功能</span>
        </td>
        <td>
            <span id="ContentPlaceHolder1_gvFlow211_Label9_1">加班</span>
            <br>
            <span id="ContentPlaceHolder1_gvFlow211_lblT_Change_1" style="color:Blue;">調休</span>
        </td>
        <td>
            <span id="ContentPlaceHolder1_gvFlow211_lblOT_Minute_1">2.28</span>&nbsp;
            <br>
            <span id="ContentPlaceHolder1_gvFlow211_lblChange_Minute_1"> </span>&nbsp;
        </td>
        <td><span id="ContentPlaceHolder1_gvFlow211_lblOT_Manhour_1">2.17</span></td>
        <td><span id="ContentPlaceHolder1_gvFlow211_lblOT_Monhour_1">30.17</span></td>
        <td><span id="ContentPlaceHolder1_gvFlow211_lblProcess_Flag_Text_1">簽核完成</span></td>
    </tr>
</table>
"""


def main():
    logger.info("=" * 80)
    logger.info("開始測試個人記錄解析")
    logger.info("=" * 80)

    # 1. 解析 HTML
    parser = PersonalRecordParser()
    records = parser.parse_records(test_html)

    logger.info("\n解析結果:")
    logger.info(f"總共解析到 {len(records)} 筆記錄\n")

    for i, record in enumerate(records, 1):
        logger.info(f"--- 記錄 {i} ---")
        logger.info(f"  日期: {record['date']}")
        logger.info(f"  內容: {record['content']}")
        logger.info(f"  狀態: {record['status']}")
        logger.info(f"  類型: {record['report_type']}")
        logger.info(f"  申報時數: {record['overtime_hours']} hr")
        logger.info(f"  當月累計: {record['monthly_total']} hr")
        logger.info(f"  當季累計: {record['quarterly_total']} hr")
        logger.info("")

    # 2. 驗證欄位名稱
    logger.info("=" * 80)
    logger.info("驗證欄位名稱")
    logger.info("=" * 80)

    if records:
        sample = records[0]
        expected_keys = [
            "date",
            "content",
            "status",
            "report_type",
            "overtime_hours",
            "monthly_total",
            "quarterly_total",
        ]

        logger.info("\n期望的欄位:")
        for key in expected_keys:
            has_key = key in sample
            value = sample.get(key, "N/A")
            status = "✅" if has_key else "❌"
            logger.info(f"  {status} {key}: {value}")

    # 3. 測試資料合併
    logger.info("\n" + "=" * 80)
    logger.info("模擬資料合併流程")
    logger.info("=" * 80)

    # 模擬異常記錄
    anomaly_records = [
        {
            "date": "2025/11/27",
            "punch_range": "09:00~19:31",
            "overtime_hours": 2.5,
            "description": "異常",
        }
    ]

    # 建立索引
    personal_by_date = {r["date"]: r for r in records}

    logger.info("\n個人記錄索引:")
    for date, record in personal_by_date.items():
        logger.info(f"  {date}:")
        logger.info(f"    - overtime_hours: {record.get('overtime_hours')}")
        logger.info(f"    - report_type: {record.get('report_type')}")
        logger.info(f"    - monthly_total: {record.get('monthly_total')}")
        logger.info(f"    - quarterly_total: {record.get('quarterly_total')}")

    logger.info("\n合併結果:")
    for anomaly in anomaly_records:
        date = anomaly["date"]
        personal = personal_by_date.get(date)

        if personal:
            logger.info(f"  日期 {date} 有對應個人記錄:")
            logger.info(
                f"    - 使用欄位 'overtime_hours': {personal.get('overtime_hours')}"
            )
            logger.info(f"    - 使用欄位 'report_type': {personal.get('report_type')}")
            logger.info(f"    - ❌ 錯誤欄位 'hours': {personal.get('hours', 'N/A')}")
            logger.info(f"    - ❌ 錯誤欄位 'type': {personal.get('type', 'N/A')}")
        else:
            logger.info(f"  日期 {date} 無對應個人記錄")

    logger.info("\n" + "=" * 80)
    logger.info("測試完成")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
