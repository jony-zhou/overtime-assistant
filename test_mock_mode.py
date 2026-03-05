"""
測試假數據生成器
"""

from src.utils.mock_data import MockDataGenerator


def test_mock_data_generation():
    """測試假數據生成"""
    print("=== 測試假數據生成 ===\n")

    # 生成出勤記錄
    print("1. 生成出勤記錄...")
    attendance_records = MockDataGenerator.generate_attendance_records(10)
    print(f"   ✓ 生成 {len(attendance_records)} 筆出勤記錄")
    if attendance_records:
        print(f"   範例: {attendance_records[0].date} - {attendance_records[0].overtime_hours}h")

    # 生成個人記錄
    print("\n2. 生成個人記錄...")
    personal_records = MockDataGenerator.generate_personal_records(10)
    print(f"   ✓ 生成 {len(personal_records)} 筆個人記錄")
    if personal_records:
        print(f"   範例: {personal_records[0].date} - {personal_records[0].overtime_hours}h")

    # 生成個人記錄統計
    print("\n3. 生成個人記錄統計...")
    personal_summary = MockDataGenerator.generate_personal_summary(personal_records)
    print(f"   ✓ 總筆數: {personal_summary.total_records}")
    print(f"   ✓ 總時數: {personal_summary.total_overtime_hours:.1f}h")
    print(f"   ✓ 平均時數: {personal_summary.average_overtime_hours:.1f}h")

    # 生成打卡記錄
    print("\n4. 生成打卡記錄...")
    punch_records = MockDataGenerator.generate_punch_records(10)
    print(f"   ✓ 生成 {len(punch_records)} 筆打卡記錄")
    if punch_records:
        print(f"   範例: {punch_records[0].date} - {len(punch_records[0].punch_times)} 次打卡")

    # 生成加班報表
    print("\n5. 生成加班報表...")
    report = MockDataGenerator.generate_overtime_report(attendance_records)
    print(f"   ✓ 總加班時數: {report.total_overtime_hours:.1f}h")
    print(f"   ✓ 加班天數: {report.overtime_days}")
    print(f"   ✓ 平均加班: {report.average_overtime_hours:.1f}h")

    # 生成申報記錄
    print("\n6. 生成申報記錄...")
    submission_records = MockDataGenerator.generate_overtime_submissions(10)
    print(f"   ✓ 生成 {len(submission_records)} 筆申報記錄")
    not_submitted = sum(1 for r in submission_records if not r.is_submitted)
    print(f"   ✓ 未申報: {not_submitted} 筆")
    print(f"   ✓ 已申報: {len(submission_records) - not_submitted} 筆")

    print("\n=== 測試完成 ✓ ===")


if __name__ == "__main__":
    test_mock_data_generation()
