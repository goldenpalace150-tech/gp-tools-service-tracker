from flask import Flask, render_template

app = Flask(__name__)

def get_tv_queue():
    # Placeholder data to test the TV screen before connecting Google Sheets
    data = [
        {"service_id": "S106", "tool_name": "صاروخ جلخ 9 بوصة", "reported_issue": "فاصل كهرباء", "status": "قيد المعالجة (In Progress)", "priority": "عاجل", "days": 1, "remarks": ""},
        {"service_id": "D204", "tool_name": "مثقب 650 واط", "reported_issue": "صوت خشن", "status": "قيد الانتظار", "priority": "عادي", "days": 4, "remarks": "بانتظار رولمان"},
        {"service_id": "V011", "tool_name": "مضخة ماء", "reported_issue": "تهريب", "status": "قيد المعالجة (In Progress)", "priority": "عادي", "days": 0, "remarks": ""}
    ]
    
    # Sort data: Urgent first, then by days delayed
    sorted_data = sorted(data, key=lambda x: (x['priority'] != 'عاجل', -x['days']))
    return sorted_data

@app.route('/tv')
def tv_display():
    jobs = get_tv_queue()
    return render_template('tv.html', jobs=jobs)

if __name__ == '__main__':
    # Run server on local network
    app.run(host='0.0.0.0', port=5000, debug=True)
