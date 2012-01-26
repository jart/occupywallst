r"""

    tranarchy.management.commands.minify
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Minifies JS/CSS/PNG media files.

    Usage: tranarchy minify APP ...

    You specify a list of Django apps as arguments.  This program finds the
    files by searching $MEDIA_DIR/$APP_NAME/{js,css,img}/.  The
    .min.js file extension is used for minified files.  No new files need
    to be created to optimize PNG.

    Minification is done using:

    - Javascript: slimit_
    - CSS: cssmin_
    - PNG: optipng_ (if available)

    Please don't put third party libraries like jQuery in your app's media
    folder because we shouldn't be minimizing them.  Put vendor libraries in
    $MEDIA_DIR/{js,css,img}/.

    .. _slimit: http://pypi.python.org/pypi/slimit
    .. _cssmin: http://pypi.python.org/pypi/cssmin
    .. _optipng: http://optipng.sourceforge.net/

"""

import os
import sys
from glob import glob
from subprocess import call
from optparse import make_option


from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    args = 'APP ...'
    help = __doc__
    option_list = BaseCommand.option_list + (
        make_option(
            '--no-mangle', action='store_false', dest='mangle',
            default=True, help="Don't mangle javascript variables"),
        make_option(
            '--copyright', action='store_true', dest='copyright',
            default=False, help=("Preserve first comment in file about "
                                 "imaginary property")),
    )

    def handle(self, *args, **options):
        mroot = settings.MEDIA_ROOT
        mangle = options['mangle']
        copyright = options['copyright']
        toto_before = 0
        toto_after = 0

        if not args:
            raise CommandError('Please specify an app name!')

        try:
            from slimit import minify
        except ImportError:
            raise CommandError('Please run: pip install slimit')

        try:
            from cssmin import cssmin
        except ImportError:
            raise CommandError('Please run: pip install cssmin')

        for app in args:
            for ext, funk in (('js', lambda s: minify(s, mangle=mangle)),
                              ('css', lambda s: cssmin(s))):
                noms = glob('%s/%s/%s/*.%s' % (mroot, app, ext, ext))
                for nom in [nom for nom in noms if '.min.' not in nom]:
                    before = os.stat(nom).st_size
                    toto_before += before
                    sys.stdout.write('minifying %s...' % (nom))
                    try:
                        with open(nom) as fin:
                            data = fin.read()
                            res = funk(data)
                            if copyright and data.startswith('/*'):
                                res = data[:data.index('*/') + 2] + res
                    except Exception, exc:
                        sys.stdout.write('%r\n' % (exc))
                    else:
                        after = len(res)
                        toto_after += after
                        with open(nom[:-len(ext)] + 'min.' + ext, 'w') as fout:
                            fout.write(res)
                        pct = int(float(after) / before * 100)
                        sys.stdout.write('OK (%d%% orig size)\n' % (pct))

        sys.stdout.write(
            'total js/css reduction: %dkB -> %dkB (%d%% orig size)\n' % (
                int(float(toto_before) / 1024),
                int(float(toto_after) / 1024),
                int(float(toto_after) / toto_before * 100)))

        pngs = []
        for app in args:
            pngs += glob('%s/%s/img/*.png' % (mroot, app))
            pngs += glob('%s/%s/img/*/*.png' % (mroot, app))
            pngs += glob('%s/%s/img/*/*/*.png' % (mroot, app))
        if pngs:
            sys.stdout.write('optimizing all your png files...')
            try:
                if call(['optipng', '-quiet'] + pngs) != 0:
                    sys.stdout.write('FAIL\n')
            except Exception, exc:
                if isinstance(exc, OSError) and exc.errno == 2:
                    sys.stdout.write('optipng not installed!\n'
                                     'sudo apt-get install optipng\n')
                else:
                    sys.stdout.write('%r\n' % (exc))
            else:
                sys.stdout.write('OK\n')
