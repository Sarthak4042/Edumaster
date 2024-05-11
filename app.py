# import flast module
from flask import Flask, render_template, request
import pandas as pd
from jinja2 import Environment, FileSystemLoader
from web3 import Web3, HTTPProvider
import firebase_admin
from firebase_admin import credentials, auth
from firebase_admin import firestore
import subprocess
import json
from solcx import compile_standard
import pdfkit
from firebase_admin import db as firebase_db
config = pdfkit.configuration(wkhtmltopdf='/usr/local/bin/wkhtmltopdf')

ganache_url = "http://127.0.0.1:7545"  # Update with your Ganache URL
web3 = Web3(Web3.HTTPProvider(ganache_url))

# Initialize Firebase Admin SDK
cred = credentials.Certificate('edumaster-verify-firebase-adminsdk-s1hb1-2a1902ed60.json')
firebase_admin.initialize_app(cred)
db = firestore.client()

firebase_admin.initialize_app(cred, name='my-rtdb-app', options={
    'databaseURL': 'https://edumaster-verify-default-rtdb.firebaseio.com'
})



# instance of flask application
app = Flask(__name__ ,template_folder='templates', static_folder='static')

# home route that returns below text when root url is accessed
@app.route("/")
def index():
    return render_template('start.html')

@app.route('/faculty_login', methods=['GET', 'POST'])
def faculty_login():
    return render_template('facutylogin.html')

@app.route('/student_login', methods=['GET', 'POST'])
def student_login():
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    return render_template('register.html')

@app.route('/verify', methods=['GET', 'POST'])
def verify():
    return render_template('verify.html')

@app.route('/forgot', methods=['GET', 'POST'])
def forgot():
    return render_template('forgot.html')

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    return render_template('student_newdash.html')

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    return render_template('student_profile.html')

@app.route('/certificates', methods=['GET', 'POST'])
def certificates():
    return render_template('student_certificates.html')

@app.route('/marksheets', methods=['GET', 'POST'])
def marksheets():
    return render_template('student_marksheets.html')

@app.route('/fdash', methods=['GET', 'POST'])
def fdash():
    return render_template('Faculty_Dashboard.html')

@app.route('/fmarks', methods=['GET', 'POST'])
def fmarks():
    return render_template('marksheets.html')

@app.route('/fassign', methods=['GET', 'POST'])
def fassign():
    return render_template('assign.html')
	
@app.route('/fcerti', methods=['GET', 'POST'])
def fcerti():
    return render_template('generate_certificates.html')

@app.route('/sem3', methods=['GET', 'POST'])
def sem3():
    return render_template('sem3.html')

@app.route('/sem4', methods=['GET', 'POST'])
def sem4():
    return render_template('sem4.html')

@app.route('/sem5', methods=['GET', 'POST'])
def sem5():
    return render_template('sem5.html')

@app.route('/sem6', methods=['GET', 'POST'])
def sem6():
    return render_template('sem6.html')

@app.route('/certi_temp', methods=['GET', 'POST'])
def certi_temp():
    return render_template('marks_template.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    return render_template('contact.html')

# Compile the smart contract
contract_source_code = '''
pragma solidity ^0.8.0;

contract UserData {
    struct User {
        string name;
        string examination;
        string seatNumber;
        string markSheet;
    }

    mapping(address => User) userData;

    function setUserData(string memory _name, string memory _examination, string memory _seatNumber, string memory _markSheet) public {
        userData[msg.sender] = User(_name, _examination, _seatNumber, _markSheet);
    }

    function getUserData(address user) public view returns (string memory, string memory, string memory, string memory) {
        User memory user = userData[user];
        return (user.name, user.examination, user.seatNumber, user.markSheet);
    }
}
'''

compiled_sol = compile_standard(
    {
        "language": "Solidity",
        "sources": {"UserData.sol": {"content": contract_source_code}},
        "settings": {"outputSelection": {"*": {"*": ["*"]}}},
    },
    solc_version="0.8.0",
)

contract_interface = compiled_sol["contracts"]["UserData.sol"]["UserData"]

# Deploy the contract
contract = web3.eth.contract(abi=contract_interface["abi"], bytecode=contract_interface["evm"]["bytecode"]["object"])
YOUR_ACCOUNT_ADDRESS = "0xCeAAeD4BfBC02D4267476577b83e1c41217710D3"
tx_hash = contract.constructor().transact({'from': YOUR_ACCOUNT_ADDRESS})
tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
contract_address = tx_receipt.contractAddress

# Interact with the contract
contract_instance = web3.eth.contract(address=contract_address, abi=contract_interface["abi"])



@app.route('/process_csv', methods=['POST'])
def process_csv():
    # Check if a file was uploaded
    if 'csv_file' not in request.files:
        return "No file part"

    csv_file = request.files['csv_file']

    # Check if the file has a name
    if csv_file.filename == '':
        return "No selected file"

    # Read the CSV file
    df = pd.read_csv(csv_file)

    #connection = Web3(HTTPProvider('https://mainnet.infura.io/v3/6bb5c539fc0642ce8f51b373015d8fc5'))
    #marksheet_uid = connection.eth.block_number

    curl_command = 'curl https://mainnet.infura.io/v3/6bb5c539fc0642ce8f51b373015d8fc5 -X POST -H "Content-Type: application/json" -d \'{"jsonrpc":"2.0","method":"eth_getTransactionByBlockHashAndIndex","params": ["0xb3b20624f8f0f86eb50dd04688409e5cea4bd02d700bf6e79e9384d47d6a5a35","0x0"],"id":1}\''
    process = subprocess.Popen(curl_command, shell=True, stdout=subprocess.PIPE)
    output, error = process.communicate()

    # Parse the cURL command output
    output_json = json.loads(output)
    block_hash = output_json.get('result', {}).get('blockHash')


    # Load Jinja2 template
    env = Environment(loader=FileSystemLoader('templates'))
    template = env.get_template("marks_template.html")

    # Generate individual mark sheets
    for index, row in df.iterrows():
        output = template.render(
            # ... (your existing code for rendering)
            name=row['NAME'],
            examination=row['EXAMINATION'],
            held_in=row['HELD IN'],
            seat_number=row['SEAT NUMBER'],
            cgpi = row['CGPI'],
            remark = row['Remark'],
            result_declared_on = row['Result Declared on'],
            marksheet_uid = tx_hash.hex(),
            grade_ESE_1 = row['GRADE ESE/PR/OR_sub1'],
            grade_IA_1 = row['GRADE IA/TW_sub1'],
            grade_ALL_1 = row['GRADE OVERALL_sub1'],
            credit_earned_1 = row['CREDIT EARNED_sub1'],
            grade_points_1 = row['GRADE POINTS_sub1'],
            grade_ESE_2 = row['GRADE ESE/PR/OR_sub2'],
            grade_IA_2 = row['GRADE IA/TW_sub2'],
            grade_ALL_2 = row['GRADE OVERALL_sub2'],
            credit_earned_2 = row['CREDIT EARNED_sub2'],
            grade_points_2 = row['GRADE POINTS_sub2'],
            grade_ESE_3 = row['GRADE ESE/PR/OR_sub3'],
            grade_IA_3 = row['GRADE IA/TW_sub3'],
            grade_ALL_3 = row['GRADE OVERALL_sub3'],
            credit_earned_3 = row['CREDIT EARNED_sub3'],
            grade_points_3 = row['GRADE POINTS_sub3'],
            grade_ESE_4 = row['GRADE ESE/PR/OR_sub4'],
            grade_IA_4 = row['GRADE IA/TW_sub4'],
            grade_ALL_4 = row['GRADE OVERALL_sub4'],
            credit_earned_4 = row['CREDIT EARNED_sub4'],
            grade_points_4 = row['GRADE POINTS_sub4'],
            grade_ESE_5 = row['GRADE ESE/PR/OR_sub5'],
            grade_IA_5 = row['GRADE IA/TW_sub5'],
            grade_ALL_5 = row['GRADE OVERALL_sub5'],
            credit_earned_5 = row['CREDIT EARNED_sub5'],
            grade_points_5 = row['GRADE POINTS_sub5'],
            grade_ESE_6 = row['GRADE ESE/PR/OR_sub6'],
            grade_IA_6 = row['GRADE IA/TW_sub6'],
            grade_ALL_6 = row['GRADE OVERALL_sub6'],
            credit_earned_6 = row['CREDIT EARNED_sub6'],
            grade_points_6 = row['GRADE POINTS_sub6'],
            grade_ESE_7 = row['GRADE ESE/PR/OR_sub7'],
            grade_IA_7 = row['GRADE IA/TW_sub7'],
            grade_ALL_7 = row['GRADE OVERALL_sub7'],
            credit_earned_7 = row['CREDIT EARNED_sub7'],
            grade_points_7 = row['GRADE POINTS_sub7'],
            grade_ESE_8 = row['GRADE ESE/PR/OR_sub8'],
            grade_IA_8 = row['GRADE IA/TW_sub8'],
            grade_ALL_8 = row['GRADE OVERALL_sub8'],
            credit_earned_8 = row['CREDIT EARNED_sub8'],
            grade_points_8 = row['GRADE POINTS_sub8'],
            grade_ESE_9 = row['GRADE ESE/PR/OR_sub9'],
            grade_IA_9 = row['GRADE IA/TW_sub9'],
            grade_ALL_9 = row['GRADE OVERALL_sub9'],
            credit_earned_9 = row['CREDIT EARNED_sub9'],
            grade_points_9 = row['GRADE POINTS_sub9'],
            grade_ESE_10 = row['GRADE ESE/PR/OR_sub10'],
            grade_IA_10 = row['GRADE IA/TW_sub10'],
            grade_ALL_10 = row['GRADE OVERALL_sub10'],
            credit_earned_10 = row['CREDIT EARNED_sub10'],
            grade_points_10 = row['GRADE POINTS_sub10'],
        )

        # Save individual mark sheet as HTML file
        file_name = f'mark_sheet_{row["NAME"]}.html'
        with open(file_name, 'w') as f:
            f.write(output)


        # Store name and marksheet_uid in Firebase Authentication
        # try:
        #     user = auth.create_user(
        #         uid= marksheet_uid,
        #         display_name=row['NAME']
        #     )
        #     print(f'Successfully created user')
        # except Exception as e:
        #     print(f'Error creating user: {e}')
            

        # Store examination, seat number, and mark sheet data in the smart contract
        exam_seat_data = f"Name: {row['NAME']}, Examination: {row['EXAMINATION']}, Seat Number: {str(row['SEAT NUMBER'])}, Mark Sheet: {file_name}"
        transaction = contract_instance.functions.setUserData(row['NAME'], row['EXAMINATION'], str(row['SEAT NUMBER']), exam_seat_data).build_transaction({
            'chainId': 5777,
            'gas': 2000000,
            'gasPrice': web3.to_wei('50', 'gwei'),
            'nonce': web3.eth.get_transaction_count(YOUR_ACCOUNT_ADDRESS),
            })
        YOUR_PRIVATE_KEY = "0x668c5b4ca9ce2107cf13dd2d15f25cdeb92c469f0c5b6bb02ba9f5c701a2403b"
        signed_txn = web3.eth.account.sign_transaction(transaction, private_key=YOUR_PRIVATE_KEY)
        #tx_hash = web3.eth.send_raw_transaction(signed_txn.rawTransaction)
        tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
        print(f"Transaction for {row['NAME']} processed. Transaction Hash: {tx_hash.hex()}")

        
            
        try:
            # Define document reference
            doc_ref = db.collection('mark_sheets').document(file_name)

            # Create or update document with HTML content
            doc_ref.set({
                'content': output
            })

            print(f'Successfully saved mark sheet {file_name} to Firestore')

            #ref = firebase_db.reference('/mark_sheets')

            # Set data under a unique key (e.g., file_name)
            #ref.child(file_name).set({
            #    'name': row['NAME'],
            #    'examination': row['EXAMINATION'],
            #    'seat_number': row['SEAT NUMBER'],
            #    'cgpi': row['CGPI'],  # Example: storing 'CGPI' value
            #    'remark': row['Remark'],  # Example: storing 'Remark' value
                # Add other fields as needed
            #})

            #print(f'Successfully saved data for {file_name} to Firebase Realtime Database')

            # Create user in Firebase Authentication
            name = row['NAME']
            final_name = name.replace(" ", "_").lower() + '_marksheet@edumaster.com'
            user = auth.create_user(email=final_name, password=tx_hash.hex())
            print('Successfully created new user:', user.uid)


        except Exception as e:
            print(f'Error saving mark sheet {file_name} to Firestore: {e}')


    return "Files processed successfully!"

@app.route('/process_certi', methods=['POST'])
def process_certi():
    # Check if a file was uploaded
    if 'csv_file' not in request.files:
        return "No file part"

    csv_file = request.files['csv_file']

    # Check if the file has a name
    if csv_file.filename == '':
        return "No selected file"

    # Read the CSV file
    cf = pd.read_csv(csv_file)

    curl_command = 'curl https://mainnet.infura.io/v3/6bb5c539fc0642ce8f51b373015d8fc5 -X POST -H "Content-Type: application/json" -d \'{"jsonrpc":"2.0","method":"eth_getTransactionByBlockHashAndIndex","params": ["0xb3b20624f8f0f86eb50dd04688409e5cea4bd02d700bf6e79e9384d47d6a5a35","0x0"],"id":1}\''
    process = subprocess.Popen(curl_command, shell=True, stdout=subprocess.PIPE)
    output, error = process.communicate()

    # Parse the cURL command output
    output_json = json.loads(output)
    block_hash = output_json.get('result', {}).get('blockHash')

    # Load Jinja2 template
    certi_env = Environment(loader=FileSystemLoader('templates'))
    template = certi_env.get_template("Certi_template.html")

    # Generate individual mark sheets
    for index, row in cf.iterrows():
        output = template.render(
            # ... (your existing code for rendering)
            name=row['Student Name'],
            course_name=row['Course Name'],
            prof_name=row['Guide Name'],
            instructor_signature=row['Name of Instructor'],
            principal_signature = row['Name of Principal'],
            from_date = row['From Date'],
            to_date = row['End Date'],
            certificate_uid = tx_hash.hex(),
        )

        # Save individual mark sheet as HTML file
        file_name = f'certificate_{row["Student Name"]}.html'
        with open(file_name, 'w') as f:
            f.write(output)

        # Store examination, seat number, and mark sheet data in the smart contract
        exam_seat_data = f"Name: {row['Student Name']}, Course Name: {row['Course Name']}, Prof Name: {row['Guide Name']}"
        transaction = contract_instance.functions.setUserData(row['Student Name'], row['Course Name'], row['Guide Name'], exam_seat_data).build_transaction({
            'chainId': 5777,
            'gas': 2000000,
            'gasPrice': web3.to_wei('50', 'gwei'),
            'nonce': web3.eth.get_transaction_count(YOUR_ACCOUNT_ADDRESS),
            })
        YOUR_PRIVATE_KEY = "0x668c5b4ca9ce2107cf13dd2d15f25cdeb92c469f0c5b6bb02ba9f5c701a2403b"
        signed_txn = web3.eth.account.sign_transaction(transaction, private_key=YOUR_PRIVATE_KEY)
        #tx_hash = web3.eth.send_raw_transaction(signed_txn.rawTransaction)
        tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
        print(f"Transaction for {row['Student Name']} processed. Transaction Hash: {tx_hash.hex()}")

        
            
        try:
            # Define document reference
            doc_ref = db.collection('certificates').document(file_name)

            # Create or update document with HTML content
            doc_ref.set({
                'content': output
            })

            print(f'Successfully saved mark sheet {file_name} to Firestore')

            # Create user in Firebase Authentication
            name = row['Student Name']
            final_name = name.replace(" ", "_").lower() + '_certificate@edumaster.com'
            user = auth.create_user(email=final_name, password=tx_hash.hex())
            print('Successfully created new user:', user.uid)

        except Exception as e:
            print(f'Error saving mark sheet {file_name} to Firestore: {e}')



    return "Files processed successfully!"


if __name__ == '__main__': 
    app.run(debug=True)
