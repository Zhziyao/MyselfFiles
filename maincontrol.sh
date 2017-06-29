#!/bin/sh
setyamienv()
{
    if [ -n "$1" ]; then
        export YAMI_ROOT_DIR=$1
    else
        export YAMI_ROOT_DIR="/opt/yami"
    fi

    export VAAPI_PREFIX="${YAMI_ROOT_DIR}/vaapi"
    export LIBYAMI_PREFIX="${YAMI_ROOT_DIR}/libyami"
    export OMXCOMPONENT_PREFIX="${YAMI_ROOT_DIR}/omx"
    export GSTOMX_PREFIX="${YAMI_ROOT_DIR}/gst-omx"

    ADD_PKG_CONFIG_PATH="${VAAPI_PREFIX}/lib/pkgconfig/:${LIBYAMI_PREFIX}/lib/pkgconfig/:${OMXCOMPONENT_PREFIX}/lib/pkgconfig/"
    ADD_LD_LIBRARY_PATH="${VAAPI_PREFIX}/lib/:${LIBYAMI_PREFIX}/lib/:${OMXCOMPONENT_PREFIX}/lib/"
    ADD_PATH="${VAAPI_PREFIX}/bin/:${LIBYAMI_PREFIX}/bin/"

    PLATFORM_ARCH_64=`uname -a | grep x86_64`
    if [ -n "$PKG_CONFIG_PATH" ]; then
        export PKG_CONFIG_PATH="${ADD_PKG_CONFIG_PATH}:$PKG_CONFIG_PATH"
    elif [ -n "$PLATFORM_ARCH_64" ]; then
        export PKG_CONFIG_PATH="${ADD_PKG_CONFIG_PATH}:/usr/lib/pkgconfig/:/usr/lib/i386-linux-gnu/pkgconfig/"
    else 
        export PKG_CONFIG_PATH="${ADD_PKG_CONFIG_PATH}:/usr/lib/pkgconfig/:/usr/lib/x86_64-linux-gnu/pkgconfig/"
    fi
    
    export LD_LIBRARY_PATH="${ADD_LD_LIBRARY_PATH}:$LD_LIBRARY_PATH"

    export PATH="${ADD_PATH}:$PATH"


    echo "*======================current configuration============================="
    echo "* VAAPI_PREFIX:               $VAAPI_PREFIX"
    echo "* LIBYAMI_PREFIX:             ${LIBYAMI_PREFIX}"
    echo "* LD_LIBRARY_PATH:            ${LD_LIBRARY_PATH}"
    echo "* PATH:                       $PATH"
    echo "*========================================================================="

    echo "* vaapi:     git clean -dxf && ./autogen.sh --prefix=\$VAAPI_PREFIX && make -j8 && make install"
    echo "* ffmpeg:    git clean -dxf && ./configure --prefix=\$VAAPI_PREFIX && make -j8 && make install"
    echo "* libyami:   git clean -dxf && ./autogen.sh --prefix=\$LIBYAMI_PREFIX --enable-tests --enable-tests-gles && make -j8 && make install"
}

ensure_dir()
{
    path_to_be_checked=$1
    if [ ! -d ${path_to_be_checked} ]; then
        mkdir -p ${path_to_be_checked}
        if [ $? -ne 0 ]; then
            echo "Creating direction ${path_to_be_checked} failed."
            return -1
        fi
    fi

    return 0
}

mnt_mediafile ()
{
    mnt_path_dest=$1
    ensure_dir $mnt_path_dest
    checked_file=$mnt_path_dest/mediafiles/AVC/AUD_MW_E.264
    if [ ! -f ${checked_file} ]; then
        echo "mount mediafiles:"
        sudo mount -t cifs //dpwu3/media ${mnt_path_dest} -o user=dpwu3,pass=123456
        if [ $? -ne 0 ]; then
            echo "Mounting media files for verify failed."
            return -1
        fi
    fi
    echo "${checked_file}"
    if [ ! -f ${checked_file} ]; then
        echo "Mounting media files for verify failed."
        return -1
    fi

    return 0
}

mnt_ffmpeg ()
{
    mnt_path_dest=$1
    
    ensure_dir $mnt_path_dest
    checked_file=$mnt_path_dest/ffplay.c
    echo "checked_file: $checked_file"
    if [ ! -f ${checked_file} ]; then
        echo "mount ffmpeg:"
        sudo mount -t cifs //dpwu3/ffmpeg ${mnt_path_dest} -o user=dpwu3,pass=123456
        if [ $? -ne 0 ]; then
            echo "Mounting ffmpeg for verify failed."
            return -1
        fi
    fi
    if [ ! -f ${checked_file} ]; then
        echo "Mounting ffmpeg for verify failed."
        return -1
    fi
    return 0
}

cp_ffmpeg ()
{
    mnt_ffmpeg_path_src=$1
    ffmpeg_path_dest=$2
    checked_file_src=$mnt_ffmpeg_path_src/ffplay.c
    checked_file_dest=$ffmpeg_path_dest/ffplay.c
    if [ -f ${checked_file_dest} ]; then
        return 0
    fi
    if [ ! -f ${checked_file_src} ]; then
        echo "Source path smb ffmpeg is not exist!"
        return -1
    fi
    rm -rf ${ffmpeg_path_dest}
    echo "Are copying ffmpeg: "
    echo "from: ${mnt_ffmpeg_path_src}"
    echo "to: ${ffmpeg_path_dest}"
    cp -r ${mnt_ffmpeg_path_src} ${ffmpeg_path_dest}
    if [ $? -ne 0 ]; then
        echo "Copying ffmpeg files failed."
        return -1
    fi

    return 0
}



####main
export DISPLAY=:0
CURRENT_PATH=`pwd`
BIN_YAMI_VERIFY_PATH=${CURRENT_PATH}/bin_yami_verify
PATH_MEDIAS_FOR_VERIFY=${CURRENT_PATH}/medias_for_verify
SMB_PATH_FFMPEG=${CURRENT_PATH}/ffmpeg_smb
PATH_FFMPEG=${CURRENT_PATH}/ffmpeg

ensure_dir ${BIN_YAMI_VERIFY_PATH}

checke_media_file=$PATH_MEDIAS_FOR_VERIFY/mediafiles/AVC/AUD_MW_E.264
if [ ! -f ${checke_media_file} ]; then
    mnt_mediafile ${PATH_MEDIAS_FOR_VERIFY}
    if [ $? -ne 0 ]; then
        exit
    fi
    echo "mount $SMB_PATH_FFMPEG success"
fi

checke_ffmpeg_file=$PATH_FFMPEG/ffplay.c
if [ ! -f ${checke_ffmpeg_file} ]; then
    mnt_ffmpeg ${SMB_PATH_FFMPEG}
    if [ $? -ne 0 ]; then
        exit
    fi
#    ensure_dir ${PATH_FFMPEG}
    cp_ffmpeg ${SMB_PATH_FFMPEG} ${PATH_FFMPEG}
    if [ $? -ne 0 ]; then
        exit
    fi
    echo "copy ffmepg $PATH_FFMPEG success"
fi

setyamienv ${BIN_YAMI_VERIFY_PATH}
sleep 6
#${CURRENT_PATH}/control.py
#${CURRENT_PATH}/control_verify.py



