import os
import sys
import json

def test():
    if not os.path.exists('index.html'):
        print("FAIL: index.html does not exist")
        sys.exit(1)

    with open('index.html', 'r', encoding='utf-8') as f:
        html = f.read()

    print(f"File size: {len(html)/1024:.1f} KB")

    # Check key DOM elements
    required_ids = ['logo', 'hdr-period', 'hdr-turnover', 'hdr-set', 'hdr-built', 'weeklist', 'strip', 'tabs', 'view', 'footer']
    for elem_id in required_ids:
        if f'id="{elem_id}"' not in html:
            print(f"FAIL: Missing element id '{elem_id}'")
            sys.exit(1)
    print("PASS: All required DOM IDs present.")

    # Check logo is embedded
    if 'data:image/png;base64,' not in html:
        print("FAIL: Logo not embedded as base64")
        sys.exit(1)
    print("PASS: Logo properly embedded.")

    # Extract JSON DATA
    start_tag = 'const DATA = '
    end_tag = ';\n\n/* ------------------------------------------------------------------ format */'
    s_idx = html.find(start_tag)
    e_idx = html.find(end_tag)
    if s_idx == -1 or e_idx == -1:
        print("FAIL: Cannot extract JSON DATA payload")
        sys.exit(1)

    json_str = html[s_idx + len(start_tag):e_idx]
    data = json.loads(json_str)
    print(f"PASS: JSON DATA parsed successfully! Total weeks: {len(data['weeks'])}")

    # Verify all 7 required modules exist in each week
    for wid, w in data['weeks'].items():
        assert 'sectors_weekly' in w and len(w['sectors_weekly']) == 27, f"Missing sectors_weekly in {wid}"
        assert 'sectors_ytd' in w and len(w['sectors_ytd']) == 27, f"Missing sectors_ytd in {wid}"
        assert 'sectors_value' in w and len(w['sectors_value']) == 27, f"Missing sectors_value in {wid}"
        assert 'sectors_nvdr' in w and len(w['sectors_nvdr']) == 27, f"Missing sectors_nvdr in {wid}"
        assert 'set50' in w and len(w['set50']) == 50, f"Missing set50 in {wid}"
        assert 'set100' in w and len(w['set100']) == 100, f"Missing set100 in {wid}"
        assert 'top20_gainers_liquid' in w and len(w['top20_gainers_liquid']) == 20, f"Missing top20 gainers in {wid}"
        assert 'top20_losers_liquid' in w and len(w['top20_losers_liquid']) == 20, f"Missing top20 losers in {wid}"
        assert 'top20_value' in w and len(w['top20_value']) == 20, f"Missing top20 value in {wid}"

    print("PASS: All 7 required modules verified across all weeks!")
    print(f"Latest completed week: {data['defaultWeekId']}")
    latest = data['weeks'][data['defaultWeekId']]
    print(f"  Summary: SET {latest['summary']['set_close']} ({latest['summary']['set_wow_pct']:+.2f}%), Turnover: {latest['summary']['turnover_bn']:.1f} Bn THB, NVDR: {latest['summary']['nvdr_net_mb']:+.1f} M THB")
    print(f"  Top weekly sector: {latest['summary']['top_sector_name']} ({latest['summary']['top_sector_wow']:+.2f}%)")
    print(f"  Top NVDR inflow sector: {latest['summary']['top_nvdr_sector_name']} (+{latest['summary']['top_nvdr_sector_mb']:.1f} M THB)")
    print("ALL TESTS PASSED!")

if __name__ == '__main__':
    test()
