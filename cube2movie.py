####################################################################################################
# wrapper function for convenient use
####################################################################################################

__all__ = ["cube2movie"]

def cube2movie(cube,
    channels         = [],
    # figure options
    figsize          = (8,8),
    vmin             = None,
    vmax             = None,
    percentiles      = [0.25, 99.75],
    cmap             = 'RdBu_r',
    imshow_kwargs    = {},
    xlabel           = 'auto',
    ylabel           = 'auto',
    # contour options
    contourlevels    = [],
    contour_kwargs   = {},
    # channel label options
    decimals         = 1,
    channelunit      = 'auto',
    channel_kwargs   = {},
    # colorbar
    show_cbar        = True,
    cbarlabel        = 'auto',
    cbar_kwargs      = {'fraction': 0.042, 'pad': 0.04},
    # movie options
    out              = 'movie.mp4',
    fps              = 2,
    dpi              = 300,
    bitrate          = 2500,
    codec            = 'h264',
    movie_kwargs     = {},
    # preview options
    preview_movie    = False,
    repeat           = False,
    animation_kwargs = {}
    ):
    """Quickly (or rather easily) Generate movies from image cubes.

    Parameters
    ----------
    cube : str, spectral_cube.SpectralCube, astropy.io.fits.hdu.hdulist.HDUList,
           astropy.io.fits.hdu.image.PrimaryHDU
        The input cube to visualize.
    channels: list
        The channels to plot in the movie. This currently supports only lists of channel numbers.
        An empty list defaults to all channels in the cube.
        TODO: allow seletion by velocity/frequency and resampling of the cube (e.g. sum/average
        channels to get fewer frames in the movie).
        Default: []

    figsize : tuple
        Size of the figure to show the channels in inches. If you find the movie to be blurry and
        not as sharp as expected increase the figure size and maybe also increase dpi and bitrate.
        The larger the figure, the slower the movie conversion.
        Default: (8,8)
    vmin/vmax : float
        Minimum and maximum of the color transfer function. The default "vmin=None", "vmax=None"
        reverts to scaling by the given percentiles.
        Default: None
    percentiles : list
        Percentiles to automatically determine vmin and vmax from. To apply the percentiles, both
        vmin and vmax must be set to their default "None".
        Default: [0.25, 99.75]
    cmap : str
        Name of the matplotlib colormap to use.
        Default: 'RdBu_r'
    imshow_kwargs : dict
        Potential keyword arguments to be passed to ax.imshow to visualize the channel data.
        Default: {}
    xlabel/ylabel : str
        Label for the x and y axes. The default 'auto' determines them automatically from the data.
        Default: 'auto'

    contourlevels : list
        Show contours at the given levels in units of the image bunit. An empty list disables
        contours.
        Default: []
    contour_kwargs : dict
        Potential keyword arguments to be passed to ax.contour to draw the contours.
        Default: {}

    decimals : int
        Number of decimal places to round the channel velocity/frequency to. Negative numbers are
        supported.
        Default: 1
    channelunit : str
        Unit to be used for the channel velocity/frequency information. The default 'auto' uses the
        unit in the image header. This is usually 'm/s' or 'Hz' but 'km/s' or 'GHz' is most often
        preferred. The unit must be given in a notation that can be parsed by astropy.units.
        Default: 'auto'
    channel_kwargs : dict
        Potential keyword arguments to be passed to ax.text to print the channel information.
        Default: {}

    show_cbar : bool
        Show a static colorbar.
        Default: True
    cbarlabel : str
        Label text for the colorbar. The default 'auto' determines the label automatically from the
        image header.
        Default: 'auto'
    cbar_kwargs : dict
        Potential keyword arguments to be passed to fig.colorbar to add the colorbar. This option
        allows to e.g. move the colorbar from its default position to the right of the image.
        Unfortunately, there is no way to force the colorbar to the same height as the map when
        using projections (as is required for astronomical data). Luckily, there are lucky numbers
        that scale the colorbar close to correctly. 'fraction' in the range 0.032 to 0.046 give
        good results over a wide range of map aspect ratios. For more details see e.g. here on
        Stackoverflow: https://stackoverflow.com/questions/18195758/set-matplotlib-colorbar-size-to-match-graph
        Default: {'fraction': 0.042, 'pad': 0.04}

    out : str
        File name to save to movie to. Existing files are overwritten!
        Default: 'movie.mp4'
    fps : int
        Speed of the movie given by the frames per second. To follow complex datasets a low frame
        rate <10 works well. In the case of many but narrow channels, a higher rate may be better.
        Default: 2
    dpi : number
        Resolution with which the movie is rendered in dots per inch. Uses the resolution set by
        matplotlibrc by default. For movies, a lower resolution than for static figures is usually
        fine.
        Default: 300
    bitrate : number
        Bitrate of the compressed movie in kilobits per second. Higher quality comes at the cost
        of increased file size. If you find the movie to be blurry rather increase the figure size
        than the bitrate.
        Default: None
    codec : str
        Video codec to encode the movie data. For now, cube2movie uses ffmpeg as the encoder
        and only codecs supported by ffmpeg are possible. To find out which video formats and
        codecs are supported on your system, run 'ffmpeg -formats' and 'ffmpeg -codecs' from the
        command line.
        Default" 'h264'
    movie_kwargs : dict
        Potential keyword arguments to be passed to matplotlib.animation.FuncAnimation.save when
        writing the movie to disk.
        Default: {}

    preview_movie : bool
        Show a preview of the movie within an interactive matplotlib window. This preview might
        stutter and temporarily slow down python interpreter or even make it become unresponsive
        for large datasets.
        Default: False
    repeat : bool
        Repeat the preview or let it stop after playing once. Letting the animation run indefinetely
        amplifies the slow down/unresponsiveness caused by the preview.
        Default: False
    animation_kwargs : dict
        Potential keyword arguments to be passed to animation.FuncAnimation() when annimating the
        image channels for a movie.
        Default: {}


    NOTE: cube2movie temporarily disables the interactive mode of matplotlib to significantly
    speed up rendering. interactive sessions are restored to interactive mode after rendering has
    finished.

    NOTE: cube2movie supresses specific warnings from SpectralCube and ax.contour because they
    can be repeated for each channel spamming the terminal and causing extensive slow-downs. These
    warnings can be re-enabled by running cube2movie.restore_warnings('all').

    NOTE: The first frame is always not correctly set up but from the second frame on everythings
    works just fine. This has something to do with tight_layout which is required to remove extensive
    whitespace.
    """

    from .CubeToMovie import CubeToMovie

    cubemovie = CubeToMovie(cube)
    cubemovie.prepare_environment()

    # set figure properties
    cubemovie.figsize          = figsize
    cubemovie.vmin             = vmin
    cubemovie.vmax             = vmax
    cubemovie.percentiles      = percentiles
    cubemovie.cmap             = cmap
    cubemovie.imshow_kwargs    = imshow_kwargs
    cubemovie.xlabel           = xlabel
    cubemovie.ylabel           = ylabel

    # set axis labels
    cubemovie.xlabel = xlabel
    cubemovie.ylabel = ylabel

    # colorbar options
    cubemovie.show_cbar        = show_cbar
    cubemovie.cbarlabel        = cbarlabel
    cubemovie.cbar_kwargs      = cbar_kwargs

    # contour options
    cubemovie.contourlevels    = contourlevels
    cubemovie.contour_kwargs   = contour_kwargs

    # channel label options
    cubemovie.decimals         = decimals
    cubemovie.channelunit      = channelunit
    cubemovie.channel_kwargs   = channel_kwargs

    # movie options
    cubemovie.out              = out
    cubemovie.fps              = fps
    cubemovie.dpi              = dpi
    cubemovie.bitrate          = bitrate
    cubemovie.codec            = codec
    cubemovie.movie_kwargs     = movie_kwargs

    # preview options
    cubemovie.preview_movie    = preview_movie
    cubemovie.repeat           = repeat
    cubemovie.animation_kwargs = animation_kwargs

    cubemovie.select_channels(channels)
    cubemovie.set_range()
    cubemovie.set_up_plot()
    cubemovie.animate()
    cubemovie.save_movie()
    cubemovie.restore_environment()


####################################################################################################
