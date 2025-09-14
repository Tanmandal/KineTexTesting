import streamlit as st
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from pymongo.errors import OperationFailure
import extra as ex
from PIL import Image
import time

with open("Style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


st.set_page_config(
    page_title="KineTex - Dashboard",
    #page_icon="images/pokeball.png",
    #layout="wide"
)

members_db="TestDB"

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

def updatemember(roll,new_name,new_roll,new_pos,new_img_url,new_prof_url,new_bio):
    try:
        client = st.session_state.client
        db = client[members_db]
        collection = db[st.session_state.selected_domain]
        if roll!=new_roll and collection.find_one({"roll": new_roll}):
            return False
        update={
            "$set":
                {
                    "name": new_name,
                    "roll": new_roll,
                    "pos": new_pos,
                    "img_url": new_img_url,
                    "prof_url": new_prof_url,
                    "bio": new_bio
                }
            }
        collection.update_one({"roll":roll}, update)
        return True
    except Exception:
        return False

def addmember(new_name, new_roll, new_pos, new_img_url,new_prof_url,new_bio):
    try:
        client = st.session_state.client
        db = client[members_db]
        collection = db[st.session_state.selected_domain]

        # 🔎 Check if roll number already exists
        if collection.find_one({"roll": new_roll}):
            return False
        ist=ex.getDateTime()
        member = {
            "name": new_name,
            "roll": new_roll,
            "pos": new_pos,
            "img_url": new_img_url,
            "prof_url": new_prof_url,
            "bio": new_bio,
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

        new_roll=int(new_roll)
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
                if updatemember(roll,new_name,new_roll,new_pos,new_img_url,new_prof_url,new_bio):
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
            new_img_url = st.text_input("Image Link")
            new_prof_url = st.text_input("Profile Link")
            pos_list=["coordinator","associate coordinator"] if st.session_state.selected_domain=='CoreTeam' else ["member", "lead", "co-lead"]
            new_pos = st.selectbox("Position", pos_list)
            new_bio = st.text_area("Bio")

            submitted = st.form_submit_button("✅ Add")
            if submitted:
                try:
                    new_roll_int = int(new_roll)
                    if addmember(new_name, new_roll_int, new_pos, new_img_url,new_prof_url,new_bio):
                        st.success("Member Added Successfully")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Failed to Add Member")
                except ValueError:
                    st.error("Roll must be an integer")




def logedin():
    st.sidebar.header(f"Hi {st.session_state.username}!")
    kinetex=st.session_state.client[members_db] #database

    domains=kinetex.list_collection_names() #collections
    addsidebarbuttons(domains)

    st.title("Hi!")
    st.header(f"Welcome to {f'{st.session_state.selected_domain} Team' if st.session_state.selected_domain else 'Team KineTex 🎉'}")

    if(st.session_state.selected_domain):
        if st.session_state.selected_domain_access:
            new_member()
        displaytable(kinetex[st.session_state.selected_domain])


def login():
    # Check user credentials
    uri = f"mongodb+srv://{st.session_state.username}:{st.session_state.password}@testing.awcpoes.mongodb.net/?retryWrites=true&w=majority&appName=Testing"

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
