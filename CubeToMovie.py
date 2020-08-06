####################################################################################################
# class to do the work
####################################################################################################

__all__ = ["CubeToMovie"]

import numpy as np
import warnings
import matplotlib as mpl
import matplotlib.pyplot as plt

class CubeToMovie:
    """
    Base class to store the cube data and movie setup, as well as methods to perform the necessary
    steps of creating a movie of the cube.
    """

    def __init__(self, cube):
        """
        Define a bunch of defaults.
        """

        # interactive mode
        self.preview_movie = False
        self.was_interactive = False
        self.is_interactive = False
        self.preview_movie = False

        # warnings
        self.warningstatus = {'wcswarning': True, 'contourwarning': True}

        # data cube
        self.load_cube(cube)
        self.channels = np.arange(len(self.cube))

        # figure
        self.figsize = (8,8)
        self.fig = None
        self.ax  = None
        self.xlabel = 'auto'
        self.ylabel = 'auto'

        # map
        self.vmin = None
        self.vmax = None
        self.percentiles = [0.25, 99.75]
        self.cmap = 'RdBu_r'
        self.imshow_kwargs = {}

        # contours
        self.contourlevels = None
        self.contour_kwargs = {}

        # channel info (velocity/frequency)
        self.decimals = 1
        self.channelunit = 'auto'
        self.channel_kwargs = {}

        # colorbar
        self.show_cbar = True
        self.cbarlabel = self.cube.header['bunit']
        self.cbar_kwargs = {}

        # animating the channel maps
        self.repeat = False

        # saving the movie
        self.out = 'movie.mp4'
        self.writer = 'ffmpeg'
        self.fps = 2
        self.dpi = None
        self.bitrate = None
        self.codec = 'h264'
        self.metadata = {'title': 'channel maps movie', 'author':'cube2movie by GiantMolecularCloud', 'genre': 'astrophysics'}
        self.movie_kwargs = {}


    def enable_interactive(self):
        mpl.interactive(True)
        self.is_interactive = True

    def disable_interactive(self):
        """
        Disable interactive mode during movie generation.
        """
        mpl.interactive(False)
        self.is_interactive = False


    def reset_interactive(self):
        """
        If interactive was on before making the movie, turn it on again.
        """
        mpl.interactive(self.was_interactive)
        self.is_interactive = self.was_interactive


    def adjust_interactive(self):
        """
        Set the correct (non-)interactive mode and store the previous setting to restore later.
        """
        self.was_interactive = mpl.is_interactive()
        if self.preview_movie:
            self.enable_interactive()
        else:
            self.disable_interactive()


    def set_mpl_settings(self):
        self.mpl_settings = plt.rcParams
        plt.rcParams.update({'text.usetex': True,
                             'savefig.pad_inches': 0.,
                             'savefig.transparent': True,
                             'savefig.frameon': True
                            })


    def restore_mpl_settings(self):
        plt.rcParams = self.mpl_settings


    def supress_wcswarnings(self):
        from spectral_cube.utils import WCSWarning
        warnings.filterwarnings('ignore', category=WCSWarning)
        warnings.warn("\nDisabled spectralcube.utils.WCSWarning in order to not break the animation. This may suppress relevant warnings but it is necessary to not completely overwhelm python. You may re-enable the warning with restore_warnings('wcswarning').\n",
                      UserWarning,
                      stacklevel = 2
                     )
        self.warningstatus['wcswarning'] = False


    def supress_contourwarnings(self):
        warnings.filterwarnings('ignore', message="No contour levels were found within the data range.")
        warnings.warn("\nDisabled matplotlib missing contour warning. You may re-enable the warning with restore_warnings('contourwarning').\n",
                      UserWarning,
                      stacklevel = 2
                     )
        self.warningstatus['contourwarning'] = False


    def restore_warnings(self,types):
        if types=='all':
            types = ['wcswarning','contourwarning']
        if not isinstance(type, (tuple,list)):
            types = [types]
        for t in types:
            if t=='wcswarning':
                from spectral_cube.utils import WCSWarning
                warnings.simplefilter('default', category=WCSWarning)
                self.warningstatus['wcswarning': True]
                print("Re-enabled WCSWarnings.")
            if t=='contourwarning':
                warnings.simplefilter('default', message="No contour levels were found within the data range.")
                self.warningstatus['contourwarning': True]
                print("Re-enabled contour warnings.")


    def prepare_environment(self):
        """
        Set up the environment needed for nice and quick plotting: no problematic warnings,
        interactive mode as needed and further matplotlib settings set for a nice plot.
        """
        self.supress_wcswarnings()
        self.supress_contourwarnings()
        self.supress_OMPwarnings()
        self.adjust_interactive()
        self.set_mpl_settings()


    def restore_environment(self):
        """
        Restore all temporary environment settings: warnings and matplotlib.
        """
        self.reset_interactive()
        self.restore_mpl_settings()
        self.restore_warnings('all')


    def load_cube(self,cube):
        """
        Load cube from file, HDU or spectralcube.
        TODO: also read CASA images
        """
        from spectral_cube import SpectralCube
        from astropy.io import fits

        if isinstance(cube, SpectralCube):
            self.cube = cube
        elif isinstance(cube,(str,fits.hdu.hdulist.HDUList,fits.hdu.image.PrimaryHDU)):
            self.cube = SpectralCube.read(cube)
        else:
            raise TypeError("Cannot interpret input cube. Allowed: SpectralCube, HDU, HDUList or filename of fits image.")
        self.spectral_axis = self.cube.spectral_axis


    def set_range(self):
        """
        Set minimum and maximum for plotting.
        """
        def round_to_4(x):
            return round(x, -int(np.floor(np.log10(np.abs(x))))+3)

        if self.vmin==None:
            self.vmin = round_to_4( self.cube.percentile(self.percentiles[0]).value )
            print("Plotting from "+str(self.percentiles[0])+"th percentile ("+str(self.vmin)+") ", end='')
        if self.vmax==None:
            self.vmax = round_to_4( self.cube.percentile(self.percentiles[1]).value )
            print("to "+str(self.percentiles[1])+"th percentile ("+str(self.vmax)+")")


    def select_channels(self,channels):
        """
        Select the requested channels.
        TODO: allow user input, add/average channels, resample cube
        """
        self.channels = channels
        print("Selecting channels "+str(self.channels))


    def create_figure(self, channel):
        """
        TODO: figure out how to force mpl to draw already the first frame with tight_layout
        """
        self.fig = plt.figure(figsize      = self.figsize,
                              tight_layout = True
                             )
        self.ax = plt.subplot(111,
                              projection = self.cube.wcs,
                              slices     = ('x', 'y', channel)
                             )
        # self.fig.subplots_adjust(left=0, bottom=0, right=1, top=1, wspace=None, hspace=None)
        # plt.tight_layout()


    def plot_map(self, channel):
        """
        Initialize the map.
        TODO: allow for other stretches.
        """
        self.map = self.ax.imshow(self.cube[channel,:,:].value,
                             origin = 'lower',
                             cmap   = getattr(plt.cm, self.cmap),
                             vmin   = self.vmin,
                             vmax   = self.vmax,
                             **self.imshow_kwargs
                            )

    def plot_contour(self, channel):
        """
        Initialize the contours.
        """
        if self.contourlevels is not []:
            self.contour = self.ax.contour(self.cube[channel,:,:].value,
                                 levels = self.contourlevels,
                                 colors = 'k',
                                 **self.contour_kwargs
                                )

    def channel_overlay(self, channel):
        """
        Initialize the channel label overlay.
        """
        self.chan_olay = self.spectral_axis[channel]
        if self.channelunit != 'auto':
            self.chan_olay = self.chan_olay.to(self.channelunit)
        self.chanlabel = self.ax.text(0.9, 0.9, '',
                                      transform = self.ax.transAxes,
                                      ha = 'right',
                                      va = 'top',
                                      **self.channel_kwargs
                                     )

    def set_axis_labels(self):
        """
        Set the axis labels.
        """
        if self.xlabel == 'auto':
            self.xlabel = self.cube.header['ctype1']
        if self.ylabel == 'auto':
            self.ylabel = self.cube.header['ctype2']
        self.ax.set_xlabel(self.xlabel)
        self.ax.set_ylabel(self.xlabel)

    def show_colorbar(self):
        """
        Add a colorbar.
        """
        if self.show_cbar:
            self.cbar = self.fig.colorbar(self.map, **self.cbar_kwargs)
            if self.cbarlabel == 'auto':
                self.cbarlabel = self.cube.header['bunit']
            self.cbar.set_label(self.cbarlabel)
            self.cbar.add_lines(self.contour)


    def set_up_plot(self):
        """
        Assemble the base plot to be updated later.
        """

        print("Preparing channel map display ...")
        channel = 0
        self.create_figure(channel)
        self.plot_map(channel)
        self.plot_contour(channel)
        self.channel_overlay(channel)
        self.set_axis_labels()
        self.show_colorbar()


    # def init_channel(self):
    #     global contour
    #
    #     self.map.set_array(self.cube[self.channels[0],:,:].value)
    #
    #     if self.contourlevels is not []:
    #         for c in self.contour.collections:
    #             c.remove()
    #         self.contour = self.ax.contour(self.cube[self.channels[0],:,:].value,
    #                              levels = self.contourlevels,
    #                              colors = 'k',
    #                              **self.contour_kwargs
    #                             )
    #
    #     self.chan_olay = self.spectral_axis[self.channels[0]]
    #     if self.channelunit != 'auto':
    #         self.chan_olay = self.chan_olay.to(self.channelunit)
    #     self.chanlabel.set_text(("{0:."+str(self.decimals)+"f}\,{1}").format(self.chan_olay.value,self.chan_olay.unit.to_string('latex_inline')))
    #     return [self.map, self.contour, self.chanlabel]


    def plot_channel(self, channel):
        global contour

        self.map.set_array(self.cube[channel,:,:].value)

        if self.contourlevels is not []:
            for c in self.contour.collections:
                c.remove()
            self.contour = self.ax.contour(self.cube[channel,:,:].value,
                                 levels = self.contourlevels,
                                 colors = 'k',
                                 **self.contour_kwargs
                                )

        self.chan_olay = self.spectral_axis[channel]
        if self.channelunit != 'auto':
            self.chan_olay = self.chan_olay.to(self.channelunit)
        self.chanlabel.set_text(("{0:."+str(self.decimals)+"f}\,{1}").format(self.chan_olay.value,self.chan_olay.unit.to_string('latex_inline')))
        return [self.map, self.contour, self.chanlabel]


    def animate(self):
        """
        Run the animation.
        """
        import matplotlib.animation as animation
        print("Animating ...")
        self.movie = animation.FuncAnimation(self.fig,
                                        func      = self.plot_channel,
                                        frames    = self.channels,
                                        # init_func = self.init_channel,
                                        interval  = 1/self.fps*1000,                # in milliseconds
                                        repeat    = self.repeat,
                                        blit      = False,                          # must be false due to contour animation
                                        cache_frame_data = True                     # keep memory impact low
                                       )


    def save_movie(self):
        """
        Save the animation as a movie file.
        TODO: fix potential problems with writers.
                imagemagick: TypeError: 'str' object is not callable
                pillow: ValueError: buffer is not large enough
                ffmpeg: may need to specify path to ffmpeg in plt.rcParams['animation.ffmpeg_path'] = '/usr/local/bin/ffmpeg'
        """
        from astropy.utils.console import ProgressBar

        warnings.warn("\nOnly ffmpeg is supported at the moment to write out the movie. If saving fails, make sure matplotlib can find your ffmpeg installation. You may need to set plt.rcParams['animation.ffmpeg_path'] = '/usr/bin/ffmpeg' to the appropriate path returned by 'which ffmpeg'.\n",
                      UserWarning,
                      stacklevel = 2
                     )

        def update_progressbar(current_frame, total_frames):
            bar.update()

        print("Saving frames ...")
        with ProgressBar(len(self.channels)) as bar:
            self.movie.save(self.out,
                        writer  = self.writer,
                        fps     = self.fps,
                        dpi     = self.dpi,
                        bitrate = self.bitrate,
                        codec   = self.codec,
                        progress_callback = update_progressbar,
                        metadata   = self.metadata,
                        **self.movie_kwargs
                       )
        print("Movie saved as "+self.out)

    def stop_animation(self):
        """
        Stop the currently running animation.
        TODO: implement stop on click in interactive mode
        """
        self.movie.event_source.stop()

    def start_animation(self):
        """
        (Re-)start the current animation.
        TODO: implement start on click in interactive mode
        """
        self.movie.event_source.start()


####################################################################################################
