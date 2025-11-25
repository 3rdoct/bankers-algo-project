import streamlit as st
import pandas as pd
import numpy as np

# 1. ฟังก์ชัน ALGORITHM
def check_safety(P, R, allocation, need, available):
    r_names = [chr(ord('A') + i) for i in range(R)]
    work = np.copy(available)
    finish = np.array([False] * P)
    safe_seq = []
    
    work_log = [work.tolist()] 
    process_log = ["Initial"] 

    count = 0
    while count < P:
        found = False
        for i in range(P):
            if not finish[i] and np.all(need[i] <= work):
                # Process ทำงานได้ -> คืน Resource
                work += allocation[i] 
                finish[i] = True #บันทึกว่า Process นี้ทำเสร็จแล้ว
                safe_seq.append(f"P{i+1}") 
                count += 1
                found = True
                
                # บันทึก Log
                work_log.append(work.tolist())
                process_log.append(f"P{i+1} runs") 
                break 
        
        if not found:
            # กรณีไม่ปลอดภัย (Deadlock)
            # ส่งค่า finish ปัจจุบันกลับไป (ตัวที่ทำเสร็จแล้วจะเป็น True)
            df_work = pd.DataFrame(work_log, index=process_log, columns=r_names)
            return False, [], df_work, finish

    # กรณีปลอดภัย (Safe)
    df_work = pd.DataFrame(work_log, index=process_log, columns=r_names)
    return True, safe_seq, df_work, finish

# 2. ฟังก์ชันจัดการข้อมูล (DATA MANAGER)
def init_session():
    if 'table_id' not in st.session_state:
        st.session_state['table_id'] = 0
    if 'init_alloc' not in st.session_state:
        st.session_state['init_alloc'] = None
    if 'init_max' not in st.session_state:
        st.session_state['init_max'] = None
    if 'init_avail' not in st.session_state:
        st.session_state['init_avail'] = None

def reset_data(P, R, p_names, r_names):
    st.session_state['init_alloc'] = pd.DataFrame(None, index=p_names, columns=r_names)
    st.session_state['init_max'] = pd.DataFrame(None, index=p_names, columns=r_names)
    st.session_state['init_avail'] = pd.DataFrame(None, index=['Available'], columns=r_names)
    
    if 'need' in st.session_state: del st.session_state['need']
    st.session_state['table_id'] += 1

# 3. ส่วน USER INTERFACE
st.set_page_config(layout="wide")
st.title("โปรแกรมจำลอง Banker's Algorithm")

init_session()

st.subheader("กำหนดจำนวน Process และ Resource")
col_p, col_r = st.columns(2)
with col_p:
    P = st.number_input("จำนวน Process (n):", min_value=1, value=5)
with col_r:
    R = st.number_input("จำนวน Resource Type (m):", min_value=1, value=3)

p_names = [f'P{i+1}' for i in range(P)]
r_names = [chr(ord('A') + i) for i in range(R)]

# เช็คขนาดตาราง ถ้าเปลี่ยนให้ Reset
if st.session_state['init_alloc'] is not None:
    if st.session_state['init_alloc'].shape != (P, R):
        reset_data(P, R, p_names, r_names)
        st.rerun()
elif st.session_state['init_alloc'] is None:
    reset_data(P, R, p_names, r_names)
    st.rerun()

st.write("---")
# ปุ่ม Reset
if st.button("🔄 รีเซตข้อมูล (Reset All)", use_container_width=True, type="secondary"):
    reset_data(P, R, p_names, r_names)
    st.rerun()

alloc_key = f"alloc_{st.session_state['table_id']}"
max_key = f"max_{st.session_state['table_id']}"
avail_key = f"avail_{st.session_state['table_id']}"

#แสดงตาราง
col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("ตาราง Allocation")
    edited_alloc = st.data_editor(st.session_state['init_alloc'], key=alloc_key)

with col2:
    st.subheader("ตาราง Max")
    edited_max = st.data_editor(st.session_state['init_max'], key=max_key)

# ปุ่มคำนวณ Need
with col2:
    if st.button("คำนวณตาราง Need", type="primary", use_container_width=True):
        if edited_alloc.isnull().values.any() or edited_max.isnull().values.any():
            st.error("⚠️ กรุณากรอกข้อมูลให้ครบทุกช่อง (ห้ามมีช่องว่าง)")
            if 'need' in st.session_state: del st.session_state['need']
        else:
            try:
                alloc_arr = edited_alloc.to_numpy(dtype=int)
                max_arr = edited_max.to_numpy(dtype=int)
                need_arr = max_arr - alloc_arr
                
                if np.any(need_arr < 0):
                    st.error("❌ ข้อมูลผิดพลาด: Max ต้องมากกว่าหรือเท่ากับ Allocation")
                    if 'need' in st.session_state: del st.session_state['need']
                else:
                    st.session_state['need'] = need_arr
                    st.session_state['final_alloc'] = alloc_arr
                    st.session_state['saved_dims'] = (P, R)
                    st.success("คำนวณสำเร็จ!")
            except Exception as e:
                st.error(f"เกิดข้อผิดพลาด: {e} (กรุณากรอกเฉพาะตัวเลข)")

# แสดงตาราง Need
with col3:
    st.subheader("ตาราง Need (Max - Allocation)")
    if 'need' in st.session_state:
        if st.session_state.get('saved_dims') == (P, R):
            df_need = pd.DataFrame(st.session_state['need'], index=p_names, columns=r_names)
            st.dataframe(df_need)
        else:
            st.warning("ข้อมูลเปลี่ยน กรุณากดคำนวณใหม่")
    else:
        st.info("รอการคำนวณ...")

st.write("---")

# ส่วน Available
st.subheader("ตาราง Available")
edited_avail = st.data_editor(st.session_state['init_avail'], key=avail_key)

st.write("")

#ปุ่มคำนวณ System State
if st.button("คำนวณสถานะระบบ (Check System State)", type="primary"):
    if 'need' not in st.session_state:
        st.error("กรุณากด 'คำนวณตาราง Need' ก่อน")
    elif edited_avail.isnull().values.any():
        st.error("⚠️ กรุณากรอก Available ให้ครบ")
    else:
        try:
            need_arr = st.session_state['need']
            if 'final_alloc' in st.session_state:
                alloc_arr = st.session_state['final_alloc']
            else:
                alloc_arr = edited_alloc.to_numpy(dtype=int)

            avail_arr = edited_avail.to_numpy(dtype=int).flatten()
            
            st.header("3. ผลลัพธ์ (Output)")
            
            # คำนวณ
            is_safe, safe_seq, df_work, final_finish = check_safety(P, R, alloc_arr, need_arr, avail_arr)
            
            # 1. ตาราง Work
            st.subheader("ตาราง Work (ขั้นตอนการคำนวณ)")
            if not df_work.empty:
                st.dataframe(df_work)
            
            # 2. ตาราง Finish
            st.subheader("ตาราง Finish (สถานะสุดท้าย)")
            df_finish_show = pd.DataFrame(
                final_finish, 
                index=p_names, 
                columns=["Is Finished?"]
            )
            
            st.dataframe(
                df_finish_show,
                column_config={
                    "Is Finished?": st.column_config.CheckboxColumn(
                        "ทำสำเร็จหรือไม่?",
                        help="ถ้าติ๊กถูก แสดงว่า Process นี้ได้รับทรัพยากรและทำงานจบแล้ว",
                        disabled=True, 
                    )
                },
                use_container_width=True
            )
            
            # 3. สรุปผล
            st.subheader("สรุปผลการตรวจสอบ")
            if is_safe:
                st.success(f"✅ **Safe State** (ระบบปลอดภัย)")
                st.info(f"**Safe Sequence:** {' → '.join(safe_seq)}")
            else:
                # แสดงจำนวนที่ทำสำเร็จ
                finished_count = np.sum(final_finish)
                st.error(f"❌ **Unsafe State** (ระบบไม่ปลอดภัย / เกิด Deadlock)")
                if finished_count > 0:
                    st.warning(f"⚠️ ทำงานสำเร็จไปแล้ว {finished_count} Process (ดูตาราง Finish ด้านบน) แต่เกิด Deadlock หลังจากนั้น")
                else:
                    st.warning("⚠️ ไม่สามารถเริ่มทำงาน Process ใดได้เลย (Deadlock ตั้งแต่ต้น)")

        except Exception as e:
            st.error(f"เกิดข้อผิดพลาด: {e}")