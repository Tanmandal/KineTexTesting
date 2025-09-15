import streamlit as st
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from pymongo.errors import OperationFailure
import extra as ex
from PIL import Image
import time
import pandas as pd

with open("Style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


st.set_page_config(
    page_title="KineTex - Dashboard",
    #page_icon="images/pokeball.png",
    #layout="wide"
)

members_db="TestDB"#"members"

if 'client' not in st.session_state:
    st.session_state.client = None
# Initialize login status in session state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "login_error" not in st.session_state:
    st.session_state.login_error = ""
if "selected_domain" not in st.session_state:
    st.session_state.selected_domain = ""
if "selected_domain_access" not in st.session_state:
    st.session_state.selected_domain_access = False
if "prev_msg" not in st.session_state:
    st.session_state.prev_msg = ""

def checkAccess():
    try:
        client = st.session_state.client
        db = client[members_db]
        collection = db[st.session_state.selected_domain]

        # Try a dummy insert and rollback immediately
        with client.start_session() as session:
            with session.start_transaction():
                collection.insert_one({"test": "access_check"}, session=session)
                session.abort_transaction()  #ensures DB not polluted
        return True  # Write access available
    except OperationFailure:
        return False
    except Exception:
        return False


def bulk_add_csv():
    if "csv_key" not in st.session_state:
        st.session_state.csv_key = 0

    with st.popover("📥 Import CSV"):
        csv_file = st.file_uploader("Upload CSV file", type="csv", key=f"csv_uploader_{st.session_state.csv_key}")

        if csv_file is not None:
            try:
                df = pd.read_csv(csv_file)

                required_fields = {"time","name", "email", "img_url", "prof_url", "bio","phn_no"}
                if not required_fields.issubset(df.columns):
                    st.error(f"CSV must have columns: {', '.join(required_fields)}")
                    return

                # Preview CSV
                st.dataframe(df)

                if st.button("📩 Insert"):
                    client = st.session_state.client
                    db = client[members_db]
                    collection = db[st.session_state.selected_domain]

                    added, skipped = 0, 0
                    for member in df.to_dict("records"):
                        try:
                            # ✅ derive roll from email (don't check missing roll column)
                            email = member.get("email")
                            if pd.isna(email):
                                skipped += 1
                                continue

                            proll = email.split("@")[0]
                            member["roll"] = int(proll)   # ✅ store in roll, keep email intact

                            if "email" in member:
                                del member["email"]


                            if collection.find_one({"roll": member["roll"]}):
                                skipped += 1
                                continue

                            # handle optional fields
                            img_url = member.get("img_url")
                            member["img_url"] = "" if pd.isna(img_url) else ex.gimageconvert(str(img_url))

                            prof_url = member.get("prof_url")
                            member["prof_url"] = "" if pd.isna(prof_url) else str(prof_url)

                            # set defaults
                            member["time"] = ex.getDateTime()
                            member["pos"] = 'member'

                            collection.insert_one(member)
                            added += 1
                        except Exception as e:
                            st.error(f"Skipping row {member}: {e}")
                            skipped += 1

                    st.success(f"Imported: {added} member(s). Skipped: {skipped} (duplicates or errors).")

                    # reset uploader
                    st.session_state.csv_key += 1
                    st.rerun()

            except Exception as e:
                st.error(f"Import failed: {e}")




def addsidebarbuttons(domains):

    #for Core Team
    cdomain='CoreTeam'
    if st.sidebar.button(cdomain,key=cdomain,width="stretch"):
        st.session_state.selected_domain=cdomain
        st.session_state.selected_domain_access=checkAccess()


    for domain in domains:
        if domain!='CoreTeam':
            if st.sidebar.button(domain,key=domain,width="stretch"):
                st.session_state.selected_domain=domain
                st.session_state.selected_domain_access=checkAccess()
    #st.write(f"{st.session_state.selected_domain_access}")


def deletemember(roll):
    try:
        client = st.session_state.client
        db = client[members_db]
        collection = db[st.session_state.selected_domain]
        collection.delete_one({"roll": roll})
        return True
    except Exception:
        return False

def updatemember(roll,new_name,new_roll,new_pos,new_img_url,new_prof_url,new_bio,new_phn_no):
    try:
        client = st.session_state.client
        db = client[members_db]
        collection = db[st.session_state.selected_domain]
        if roll!=new_roll and collection.find_one({"roll": new_roll}):
            return False
        new_img_url=ex.gimageconvert(new_img_url)
        update={
            "$set":
                {
                    "name": new_name,
                    "roll": new_roll,
                    "pos": new_pos,
                    "img_url": new_img_url,
                    "prof_url": new_prof_url,
                    "bio": new_bio,
                    "phn_no": new_phn_no
                }
            }
        collection.update_one({"roll":roll}, update)
        return True
    except Exception:
        return False

def addmember(new_name, new_roll, new_pos, new_img_url,new_prof_url,new_bio,new_phn_no):
    try:
        client = st.session_state.client
        db = client[members_db]
        collection = db[st.session_state.selected_domain]

        # 🔎 Check if roll number already exists
        if collection.find_one({"roll": new_roll}):
            return False
        ist=ex.getDateTime()
        new_img_url=ex.gimageconvert(new_img_url)
        member = {
            "name": new_name,
            "roll": new_roll,
            "pos": new_pos,
            "img_url": new_img_url,
            "prof_url": new_prof_url,
            "bio": new_bio,
            "phn_no": new_phn_no,
            "time": ist
        }
        collection.insert_one(member)
        return True
    except Exception:
        return False




def viewpopover(popover,member):
    roll=member['roll']
    name=member['name']
    pos=member['pos']
    img_url=member['img_url']
    prof_url=member['prof_url']
    bio=member['bio']
    phn_no=member['phn_no']
    with popover:
        # Show image
        if img_url:
            st.image(ex.gdriveimg(img_url), width=200)
        else:
            st.image("https://upload.wikimedia.org/wikipedia/commons/1/14/No_Image_Available.jpg", width=200)

        # Editable image link with unique key
        new_img_url = st.text_input("Image Link", value=img_url, key=f"img_{roll}",disabled=not st.session_state.selected_domain_access)

        # Editable fields with unique keys
        new_name = st.text_input("Name", value=name, key=f"name_{roll}",disabled=not st.session_state.selected_domain_access)
        new_roll = st.text_input("Roll No.", value=roll, key=f"roll_{roll}",disabled=not st.session_state.selected_domain_access)
        new_phn_no = st.text_input("Phone No.", value=phn_no, key=f"phn_{roll}",disabled=not st.session_state.selected_domain_access)
        new_prof_url = st.text_input("Profile Link", value=prof_url, key=f"prof_{roll}",disabled=not st.session_state.selected_domain_access)
        new_bio = st.text_area("Bio", value=bio, key=f"bio_{roll}",disabled=not st.session_state.selected_domain_access)
        # Role selector with unique key
        if st.session_state.selected_domain_access:
            pos_list=["coordinator","associate coordinator"] if st.session_state.selected_domain=='CoreTeam' else ["member", "lead", "co-lead"]
            new_pos = st.selectbox(
                "Position",
                pos_list,
                index=pos_list.index(pos) if pos in pos_list else 0,
                key=f"pos_{roll}"
            )
        else:
            new_pos = st.text_input("Position", value=pos, key=f"pos_{roll}",disabled=not st.session_state.selected_domain_access)

        if(st.session_state.selected_domain_access):
            st.markdown("---")
            # Action buttons with unique keys
            if(f"{roll}" in st.session_state.prev_msg):
                if("Successful" in st.session_state.prev_msg):
                    st.success(st.session_state.prev_msg[0:st.session_state.prev_msg.find(f"{roll}")])
                else:
                    st.error(st.session_state.prev_msg[0:st.session_state.prev_msg.find(f"{roll}")])
                time.sleep(1)
                st.session_state.prev_msg=""
                st.rerun()


            col1, col2 = st.columns(2)
            with col1:
                update_clicked = st.button("📝 Update", key=f"update_{roll}")
            with col2:
                delete_clicked = st.button("🗑️ Delete", key=f"delete_{roll}")

            if update_clicked:
                if new_roll.isnumeric() and ("0"+str(new_phn_no)).isnumeric() and updatemember(roll,new_name,int(new_roll),new_pos,new_img_url,new_prof_url,new_bio,new_phn_no):
                    st.session_state.prev_msg = f"Update Successful {new_roll}"
                else:
                    st.session_state.prev_msg = f"Failed to Update {roll}"
                st.rerun()
            if delete_clicked:
                if deletemember(roll):
                    st.session_state.prev_msg = f"Delete Successful {new_roll}"
                else:
                    st.session_state.prev_msg = f"Failed to Delete {new_roll}"
                st.rerun()




def viewdomainrow(member):
    with st.container():
        col1,col2,col3,col4=st.columns((1,2,1,1))
        with col1:
            st.write(member['roll'])
        with col2:
            st.write(member['name'])
        with col3:
            st.write(member['pos'])
        with col4:
            popover = st.popover("view")#https://docs.streamlit.io/develop/api-reference/layout/st.popover
            if popover:
                viewpopover(popover,member)

def displaytable(domain):
    members = list(domain.find())

    if st.session_state.selected_domain=='CoreTeam':
        for coordinator in members:
            if coordinator["pos"] == "coordinator":
                viewdomainrow(coordinator)

        #co_leads=domain.find({"pos":"co_lead"})
        for asco in members:
            if asco["pos"] == "associate coordinator":
                viewdomainrow(asco)
    else:
        #leads=domain.find({"pos":"lead"})
        for lead in members:
            if lead["pos"] == "lead":
                viewdomainrow(lead)

        #co_leads=domain.find({"pos":"co_lead"})
        for co_lead in members:
            if co_lead["pos"] == "co-lead":
                viewdomainrow(co_lead)

        #members=domain.find()
        for member in members:
            if member["pos"] not in ["lead","co-lead"]:
                viewdomainrow(member)

def new_member():
    with st.popover("➕ Add Member"):
        with st.form("add_member_form", clear_on_submit=True):  # 👈 this clears automatically
            new_name = st.text_input("Name")
            new_roll = st.text_input("Roll No.")
            new_phn_no = st.text_input("Phone No.")
            new_img_url = st.text_input("Image Link")
            new_prof_url = st.text_input("Profile Link")
            pos_list=["coordinator","associate coordinator"] if st.session_state.selected_domain=='CoreTeam' else ["member", "lead", "co-lead"]
            new_pos = st.selectbox("Position", pos_list)
            new_bio = st.text_area("Bio")

            submitted = st.form_submit_button("✅ Add")
            if submitted:
                try:
                    new_roll_int = int(new_roll)
                    new_phn_no= int(new_phn_no)
                    if addmember(new_name, new_roll_int, new_pos, new_img_url,new_prof_url,new_bio,new_phn_no):
                        st.success("Member Added Successfully")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Failed to Add Member")
                except ValueError:
                    st.error("Roll/Phone no. Error")




def logedin():
    st.sidebar.header(f"Hi {st.session_state.username}!")
    kinetex=st.session_state.client[members_db] #database

    domains=kinetex.list_collection_names() #collections
    addsidebarbuttons(domains)

    st.title("Hi!")
    st.header(f"Welcome to {f'{st.session_state.selected_domain} Team' if st.session_state.selected_domain else 'Team KineTex 🎉'}")

    if(st.session_state.selected_domain):
        if st.session_state.selected_domain_access:
            with st.container():
                col1,col2=st.columns(2)
                with col1:
                    new_member()
                with col2:
                    bulk_add_csv()
        displaytable(kinetex[st.session_state.selected_domain])


def login():
    # Check user credentials
    uri = f"mongodb+srv://{st.session_state.username}:{st.session_state.password}@testing.awcpoes.mongodb.net/?retryWrites=true&w=majority&appName=Testing"
    #@cluster0.45qgj0b.mongodb.net/"
    try:
        client = MongoClient(uri, server_api=ServerApi('1'))
        client.admin.command('ping')
        #print("Pinged your deployment. You successfully connected to MongoDB!")
        st.session_state.logged_in = True
        st.session_state.login_error = ""
        st.session_state.client = client
    except OperationFailure as e:
        if(getattr(e, 'code', None)==8000):
            st.session_state.login_error = "Invalid Credentials"
    except Exception as e:
        if str(e).find('A password is required') !=-1:
            st.session_state.login_error = "Password Required"
        elif str(e).find('not valid username') !=-1:
            st.session_state.login_error = "Invalid Username"
        else:
            st.session_state.login_error = str(e)



if not st.session_state.logged_in:
    st.title("Login Page")
    username=st.text_input("Username")
    password=st.text_input("Password", type="password")
    st.session_state.username=username
    st.session_state.password=password
    st.button("Login", on_click=login)
    if st.session_state.login_error:
        st.error(st.session_state.login_error)
else:
    logedin()
