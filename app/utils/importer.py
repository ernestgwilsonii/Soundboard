import json
import os
import zipfile
import io
import uuid
from flask import current_app
from app.models import Soundboard, Sound, Tag

class Importer:
    @staticmethod
    def import_soundboard_pack(zip_stream, user_id):
        """
        Extracts a Soundboard Pack and reconstructs the soundboard in the database.
        Returns the new Soundboard object.
        """
        try:
            with zipfile.ZipFile(zip_stream, 'r') as zf:
                # 1. Validate manifest
                if 'manifest.json' not in zf.namelist():
                    raise ValueError("Invalid pack: manifest.json missing")
                
                manifest_data = zf.read('manifest.json')
                manifest = json.loads(manifest_data)
                
                # 2. Create the Soundboard
                sb_name = f"{manifest.get('name', 'Imported Board')} (Imported)"
                sb_icon = manifest.get('icon', 'fas fa-music')
                theme_color = manifest.get('theme_color', '#0d6efd')
                
                new_sb = Soundboard(name=sb_name, user_id=user_id, icon=sb_icon, 
                                   is_public=False, theme_color=theme_color)
                new_sb.save() # Gets the ID
                
                # 3. Handle custom board icon
                if 'custom_board_icon_file' in manifest:
                    icon_path_in_zip = manifest['custom_board_icon_file']
                    if icon_path_in_zip in zf.namelist():
                        ext = os.path.splitext(icon_path_in_zip)[1]
                        new_icon_name = f"icons/board_{new_sb.id}_{uuid.uuid4().hex}{ext}"
                        full_path = os.path.join(current_app.config['UPLOAD_FOLDER'], new_icon_name)
                        
                        if not os.path.exists(os.path.dirname(full_path)):
                            os.makedirs(os.path.dirname(full_path))
                            
                        with open(full_path, 'wb') as f:
                            f.write(zf.read(icon_path_in_zip))
                        
                        new_sb.icon = new_icon_name
                        new_sb.save()

                # 4. Process Tags
                for tag_name in manifest.get('tags', []):
                    new_sb.add_tag(tag_name)
                
                # 5. Process Sounds
                sb_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], str(new_sb.id))
                if not os.path.exists(sb_dir):
                    os.makedirs(sb_dir)
                    
                for s_data in manifest.get('sounds', []):
                    zip_audio_path = f"sounds/{s_data['file_name']}"
                    if zip_audio_path in zf.namelist():
                        # Save audio file
                        unique_filename = f"{uuid.uuid4().hex}_{s_data['file_name']}"
                        audio_path = os.path.join(str(new_sb.id), unique_filename)
                        full_audio_path = os.path.join(current_app.config['UPLOAD_FOLDER'], audio_path)
                        
                        with open(full_audio_path, 'wb') as f:
                            f.write(zf.read(zip_audio_path))
                            
                        # Handle custom sound icon
                        sound_icon = s_data.get('icon', 'fas fa-volume-up')
                        if 'custom_icon_file' in s_data:
                            zip_s_icon_path = s_data['custom_icon_file']
                            if zip_s_icon_path in zf.namelist():
                                ext = os.path.splitext(zip_s_icon_path)[1]
                                new_s_icon_name = f"icons/sound_{uuid.uuid4().hex}{ext}"
                                full_s_icon_path = os.path.join(current_app.config['UPLOAD_FOLDER'], new_s_icon_name)
                                
                                with open(full_s_icon_path, 'wb') as f:
                                    f.write(zf.read(zip_s_icon_path))
                                sound_icon = new_s_icon_name
                        
                        # Create Sound model
                        new_sound = Sound(
                            soundboard_id=new_sb.id,
                            name=s_data['name'],
                            file_path=audio_path,
                            icon=sound_icon,
                            display_order=s_data.get('display_order', 0),
                            volume=s_data.get('volume', 1.0),
                            is_loop=s_data.get('is_loop', False),
                            start_time=s_data.get('start_time', 0.0),
                            end_time=s_data.get('end_time')
                        )
                        new_sound.save()
                
                return new_sb
                
        except Exception as e:
            current_app.logger.error(f"Import failed: {e}")
            raise e
