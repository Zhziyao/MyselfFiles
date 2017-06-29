#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <dlfcn.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/stat.h>
#include <va.h>
#include <va_drm.h>

#include <YamiVersion.h>
#include <VideoEncoderCapi.h>

static int g_va_fd = -1;
static VADisplay g_va_display = 0;
static int g_va_major_version = 0;
static int g_va_minor_version = 0;
static VASurfaceID g_va_surface = 0;
static VAImage g_va_image;
static EncodeHandler g_handle = 0;

int main(int argc, char** argv)
{
    VAImageFormat va_image_format;
    NativeDisplay nd;
    VideoParamsCommon encVideoParams;
    VideoConfigAVCStreamFormat streamFormat;
    int index;
    int count;
    void* buf_ptr;
    VideoFrame yami_vf;
    VideoEncOutputBuffer outb;
    char *cdata;
    int cdata_max_bytes;
    int noencode;

    noencode = 0;
    count = 100;
    for (index = 0; index < argc; index++)
    {
        if (strcmp(argv[index], "--loop") == 0)
        {
            count = atoi(argv[index + 1]);
            index++;
        }
        if (strcmp(argv[index], "--noencode") == 0)
        {
            noencode = 1;
        }
    }

    cdata_max_bytes = 1024 * 1024;
    cdata = (char *) malloc(cdata_max_bytes);

    g_va_fd = open("/dev/dri/renderD128", O_RDWR);
    printf("g_va_fd %d\n", g_va_fd);
    g_va_display = vaGetDisplayDRM(g_va_fd);
    printf("g_va_display %p\n", g_va_display);
    vaInitialize(g_va_display, &g_va_major_version, &g_va_minor_version);

    for (index = 0; index < count; index++)
    {

        vaCreateSurfaces(g_va_display, VA_RT_FORMAT_YUV420, 1024, 768,
                         &g_va_surface, 1, 0, 0);
        memset(&va_image_format, 0, sizeof(va_image_format));
        va_image_format.fourcc = VA_FOURCC_NV12;
        vaCreateImage(g_va_display, &va_image_format, 1024, 768, &g_va_image);

        g_handle = createEncoder(YAMI_MIME_H264);
        memset(&nd, 0, sizeof(nd));
        nd.handle = (intptr_t) (g_va_display);
        nd.type = NATIVE_DISPLAY_VA;
        encodeSetNativeDisplay(g_handle, &nd);

        memset(&encVideoParams, 0, sizeof(encVideoParams));
        encVideoParams.size = sizeof(VideoParamsCommon);
        encodeGetParameters(g_handle, VideoParamsTypeCommon, &encVideoParams);
        encVideoParams.resolution.width = 1024;
        encVideoParams.resolution.height = 768;
        encVideoParams.rcMode = RATE_CONTROL_CQP;
        encVideoParams.rcParams.initQP = 28;
        encVideoParams.intraPeriod = 16;
        encodeSetParameters(g_handle, VideoParamsTypeCommon, &encVideoParams);
        memset(&streamFormat, 0, sizeof(streamFormat));
        streamFormat.size = sizeof(VideoConfigAVCStreamFormat);
        encodeGetParameters(g_handle, VideoConfigTypeAVCStreamFormat, &streamFormat);
        streamFormat.streamFormat = AVC_STREAM_FORMAT_ANNEXB;
        encodeSetParameters(g_handle, VideoConfigTypeAVCStreamFormat, &streamFormat);
        encodeStart(g_handle);

        vaMapBuffer(g_va_display, g_va_image.buf, &buf_ptr);
        memset(buf_ptr, 0, ((1024 * 768) * 3) / 2);
        vaUnmapBuffer(g_va_display, g_va_image.buf);
        vaPutImage(g_va_display, g_va_surface, g_va_image.image_id,
                   0, 0, 1024, 768, 0, 0, 1024, 768);
        vaSyncSurface(g_va_display, g_va_surface);

        if (noencode == 0)
        {
            memset(&yami_vf, 0, sizeof(yami_vf));
            yami_vf.surface = g_va_surface;
            encodeEncode(g_handle, &yami_vf);

            memset(&outb, 0, sizeof(outb));
            outb.data = (unsigned char *) (cdata);
            outb.bufferSize = cdata_max_bytes;
            outb.format = OUTPUT_EVERYTHING;
            encodeGetOutput(g_handle, &outb, 1);
            printf("compressed to %d\n", outb.dataSize);
        }

        encodeStop(g_handle);
        releaseEncoder(g_handle);

        vaDestroyImage(g_va_display, g_va_image.image_id);
        vaDestroySurfaces(g_va_display, &g_va_surface, 1);

        usleep(10000);
        printf("loop %d\n", index);

    }

    vaTerminate(g_va_display);
    close(g_va_fd);
    free(cdata);
    return 0;
}